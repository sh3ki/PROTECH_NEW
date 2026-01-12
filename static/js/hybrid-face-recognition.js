/**
 * Hybrid Face Recognition System
 * Manages TWO independent face recognition instances:
 * - TIME IN camera (timein-webcam, timein-overlay-canvas)
 * - TIME OUT camera (timeout-webcam, timeout-overlay-canvas)
 */

const FACE_API_MODEL_URL = window.FACE_API_MODEL_URL || 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.12/model';

class HybridFaceRecognition {
    constructor(videoId, canvasId, attendanceType, fpsCounterId, listId, countId) {
        this.videoId = videoId;
        this.canvasId = canvasId;
        this.attendanceType = attendanceType; // 'time_in' or 'time_out'
        this.fpsCounterId = fpsCounterId;
        this.listId = listId;
        this.countId = countId;
        
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.isRunning = false;
        this.processingFrame = false;
        this.currentDetections = [];
        this.frameCount = 0;
        this.fps = 0;
        this.lastFpsUpdate = Date.now();
        this.recognitionCooldown = new Map();
        this.cooldownMs = 5000;
        this.resizeObserver = null;
        this.scaleX = 1;
        this.scaleY = 1;
        this.processIntervalMs = 500;
        this.lastRecognitionTime = 0;
        this.lastResults = [];
        this.modelsLoaded = false;
        this.detectorOptions = null;
        this.previousDetections = [];
        this.motionThreshold = 0.012; // Minimum normalized motion to accept as live
        this.maxStaticFrames = 6; // Frames a face can stay static before being blocked
        this.blinkEarThreshold = 0.21; // Eye Aspect Ratio threshold for blink detection
        this.blinkConsecutiveFrames = 2;
        this.spoofProofEnabled = window.SPOOF_PROOF_ENABLED !== false;
        
        // Track recognized students
        this.recognizedStudents = new Map();
    }

    async initialize() {
        try {
            this.video = document.getElementById(this.videoId);
            this.canvas = document.getElementById(this.canvasId);

            if (!this.video || !this.canvas) {
                console.error(`[${this.attendanceType}] Video or canvas element not found.`);
                return;
            }

            this.ctx = this.canvas.getContext('2d', { alpha: true });
            if (!this.ctx) {
                console.error(`[${this.attendanceType}] Unable to obtain 2D canvas context.`);
                return;
            }

            await this.loadModels();
            if (!this.modelsLoaded) {
                console.error(`[${this.attendanceType}] face-api models failed to load.`);
                return;
            }

            this.registerVideoEvents();

            if (this.video.readyState >= 2 && !this.video.paused && !this.video.ended) {
                this.onVideoReady();
            }
            
            console.log(`[${this.attendanceType}] Face recognition initialized successfully.`);
        } catch (error) {
            console.error(`[${this.attendanceType}] Failed to initialize face recognition:`, error);
        }
    }

    async loadModels() {
        if (this.modelsLoaded) {
            return;
        }

        if (typeof faceapi === 'undefined') {
            console.error(`[${this.attendanceType}] face-api.js is not available on window.`);
            return;
        }

        try {
            // Models are shared globally, so only load once
            if (!window.faceApiModelsLoaded) {
                await Promise.all([
                    faceapi.nets.tinyFaceDetector.loadFromUri(FACE_API_MODEL_URL),
                    faceapi.nets.faceLandmark68Net.loadFromUri(FACE_API_MODEL_URL),
                    faceapi.nets.faceRecognitionNet.loadFromUri(FACE_API_MODEL_URL)
                ]);
                window.faceApiModelsLoaded = true;
                console.log('face-api models loaded (shared).');
            }
            
            this.detectorOptions = new faceapi.TinyFaceDetectorOptions({
                inputSize: 224,
                scoreThreshold: 0.5
            });
            this.modelsLoaded = true;
            console.log(`[${this.attendanceType}] face-api models ready.`);
        } catch (error) {
            console.error(`[${this.attendanceType}] Error loading face-api models:`, error);
        }
    }

    registerVideoEvents() {
        const handleReady = () => this.onVideoReady();
        this.video.addEventListener('loadedmetadata', handleReady);
        this.video.addEventListener('play', handleReady);

        if (typeof ResizeObserver !== 'undefined') {
            this.resizeObserver = new ResizeObserver(() => this.syncCanvasSize());
            this.resizeObserver.observe(this.video);
        } else {
            window.addEventListener('resize', () => this.syncCanvasSize());
        }
    }

    onVideoReady() {
        if (!this.video.videoWidth || !this.video.videoHeight) {
            return;
        }

        this.syncCanvasSize();

        if (!this.isRunning) {
            this.isRunning = true;
            requestAnimationFrame(() => this.recognitionLoop());
            console.log(`[${this.attendanceType}] Face recognition loop started.`);
        }
    }

    syncCanvasSize() {
        if (!this.video.videoWidth || !this.video.videoHeight) {
            return;
        }

        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;

        const rect = this.video.getBoundingClientRect();
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.pointerEvents = 'none';

        this.scaleX = this.canvas.width / this.video.videoWidth;
        this.scaleY = this.canvas.height / this.video.videoHeight;
    }

    async recognitionLoop() {
        if (!this.isRunning) {
            return;
        }

        this.drawDetections();

        if (!this.processingFrame) {
            this.processingFrame = true;
            this.processFrame()
                .catch(error => console.error(`[${this.attendanceType}] Error processing frame:`, error))
                .finally(() => {
                    this.processingFrame = false;
                });
        }

        requestAnimationFrame(() => this.recognitionLoop());
    }

    drawDetections() {
        if (!this.ctx) {
            return;
        }

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        for (const detection of this.currentDetections) {
            if (detection.status === 'matched') {
                const result = detection.result || {};
                const lines = [];
                const lrn = result.lrn || result.student_id;
                const segments = [];
                if (result.first_name) {
                    segments.push(result.first_name);
                }
                if (result.last_name) {
                    segments.push(result.last_name);
                }
                const name = result.name || segments.join(' ').trim();

                if (lrn) {
                    lines.push('LRN: ' + lrn);
                }
                if (name) {
                    lines.push(name);
                }
                if (typeof result.confidence === 'number') {
                    lines.push('Confidence: ' + (result.confidence * 100).toFixed(1) + '%');
                }

                this.drawStyledBox(detection.box, {
                    stroke: '#22C55E',
                    fill: 'rgba(34, 197, 94, 0.25)',
                    labelLines: lines.length ? lines : ['Recognized'],
                    labelColor: '#000000'
                });
            } else if (detection.status === 'needs_motion') {
                this.drawStyledBox(detection.box, {
                    stroke: '#F97316',
                    fill: 'rgba(249, 115, 22, 0.18)',
                    labelLines: ['Move face to verify'],
                    labelColor: '#FFFFFF'
                });
            } else if (detection.status === 'spoof') {
                this.drawStyledBox(detection.box, {
                    stroke: '#EF4444',
                    fill: 'rgba(239, 68, 68, 0.25)',
                    labelLines: ['Spoof blocked'],
                    labelColor: '#FFFFFF'
                });
            } else {
                this.drawStyledBox(detection.box, {
                    stroke: '#EF4444',
                    fill: 'rgba(239, 68, 68, 0.25)',
                    labelLines: ['UNAUTHORIZED'],
                    labelColor: '#FFFFFF'
                });
            }
        }
    }

    drawStyledBox(box, options) {
        if (!box) {
            return;
        }

        const config = Object.assign({
            stroke: '#FFFFFF',
            fill: null,
            labelLines: [],
            labelColor: '#FFFFFF'
        }, options || {});

        const start = box.start || [0, 0];
        const end = box.end || [0, 0];

        const x1 = Math.max(0, Math.min(start[0], this.canvas.width));
        const y1 = Math.max(0, Math.min(start[1], this.canvas.height));
        const x2 = Math.max(0, Math.min(end[0], this.canvas.width));
        const y2 = Math.max(0, Math.min(end[1], this.canvas.height));

        const width = Math.max(0, x2 - x1);
        const height = Math.max(0, y2 - y1);

        this.ctx.save();

        if (config.fill) {
            this.ctx.fillStyle = config.fill;
            this.ctx.fillRect(x1, y1, width, height);
        }

        this.ctx.strokeStyle = config.stroke;
        this.ctx.lineWidth = 4;
        this.ctx.strokeRect(x1, y1, width, height);

        if (config.labelLines.length) {
            const lineHeight = 18;
            const padding = 8;
            const boxHeight = config.labelLines.length * lineHeight + padding * 2;
            const labelWidth = Math.max(width, 140);
            let labelTop = y1 - boxHeight - 4;
            if (labelTop < 0) {
                labelTop = y1 + 4;
            }

            this.ctx.fillStyle = config.stroke;
            this.ctx.fillRect(x1, labelTop, labelWidth, boxHeight);

            this.ctx.fillStyle = config.labelColor;
            this.ctx.font = 'bold 14px Arial';
            config.labelLines.forEach((line, index) => {
                this.ctx.fillText(line, x1 + padding, labelTop + padding + (index + 1) * lineHeight - 4);
            });
        }

        this.ctx.restore();
    }

    evaluateLiveness(detections) {
        if (!this.spoofProofEnabled) {
            const liveResults = detections.map(detection => {
                const box = detection.detection.box;
                const landmarks = detection.landmarks.positions.map(pt => ({ x: pt.x, y: pt.y }));
                const center = { x: box.x + box.width / 2, y: box.y + box.height / 2 };
                return {
                    status: 'live',
                    motionScore: 1,
                    blink: { detected: false, ear: 1 },
                    landmarks,
                    center,
                    staticFrames: 0
                };
            });
            this.previousDetections = liveResults.map(item => ({ center: item.center, landmarks: item.landmarks, staticFrames: 0 }));
            return liveResults;
        }

        const results = [];
        const previous = [...this.previousDetections];
        const usedPrev = new Set();

        detections.forEach(detection => {
            const box = detection.detection.box;
            const landmarks = detection.landmarks.positions.map(pt => ({ x: pt.x, y: pt.y }));
            const center = {
                x: box.x + box.width / 2,
                y: box.y + box.height / 2
            };

            const prevIndex = this.matchPreviousDetection(center, previous, usedPrev);
            const prev = prevIndex !== -1 ? previous[prevIndex] : null;

            const centerDelta = prev ? { dx: center.x - prev.center.x, dy: center.y - prev.center.y } : { dx: 0, dy: 0 };

            const motionScore = prev ? this.computeMotionScore(prev.landmarks, landmarks, box, centerDelta) : 0;
            const blinkInfo = this.detectBlink(landmarks);

            let staticFrames = prev ? prev.staticFrames : 0;
            let status = 'liveness_required';

            if (motionScore >= this.motionThreshold || blinkInfo.detected) {
                staticFrames = 0;
                status = 'live';
            } else {
                staticFrames += 1;
                if (staticFrames >= this.maxStaticFrames) {
                    status = 'spoof';
                }
            }

            results.push({
                status,
                motionScore,
                blink: blinkInfo,
                landmarks,
                center,
                staticFrames
            });
        });

        this.previousDetections = results.map(item => ({
            center: item.center,
            landmarks: item.landmarks,
            staticFrames: item.staticFrames
        }));

        return results;
    }

    matchPreviousDetection(center, previous, usedPrev) {
        let bestIndex = -1;
        let bestDistance = Infinity;

        previous.forEach((prev, idx) => {
            if (usedPrev.has(idx)) {
                return;
            }
            const dx = center.x - prev.center.x;
            const dy = center.y - prev.center.y;
            const distance = Math.hypot(dx, dy);
            if (distance < bestDistance) {
                bestDistance = distance;
                bestIndex = idx;
            }
        });

        if (bestIndex !== -1) {
            usedPrev.add(bestIndex);
        }

        return bestIndex;
    }

    computeMotionScore(prevLandmarks, currentLandmarks, box, centerDelta) {
        if (!prevLandmarks || !currentLandmarks || !prevLandmarks.length || !currentLandmarks.length) {
            return 0;
        }

        const len = Math.min(prevLandmarks.length, currentLandmarks.length);
        let total = 0;

        for (let i = 0; i < len; i++) {
            const dx = (currentLandmarks[i].x - prevLandmarks[i].x) - centerDelta.dx;
            const dy = (currentLandmarks[i].y - prevLandmarks[i].y) - centerDelta.dy;
            total += Math.hypot(dx, dy);
        }

        const average = total / len;
        const normalization = Math.max(box.width + box.height, 1);
        return average / normalization;
    }

    detectBlink(landmarks) {
        if (!landmarks || landmarks.length < 48) {
            return { detected: false, ear: 1 };
        }

        const leftEye = [36, 37, 38, 39, 40, 41].map(i => landmarks[i]);
        const rightEye = [42, 43, 44, 45, 46, 47].map(i => landmarks[i]);

        const leftEAR = this.calculateEAR(leftEye);
        const rightEAR = this.calculateEAR(rightEye);
        const ear = (leftEAR + rightEAR) / 2;

        return {
            detected: ear < this.blinkEarThreshold,
            ear
        };
    }

    calculateEAR(eyePoints) {
        if (!eyePoints || eyePoints.length < 6) {
            return 1;
        }

        const vertical1 = Math.hypot(eyePoints[1].x - eyePoints[5].x, eyePoints[1].y - eyePoints[5].y);
        const vertical2 = Math.hypot(eyePoints[2].x - eyePoints[4].x, eyePoints[2].y - eyePoints[4].y);
        const horizontal = Math.hypot(eyePoints[0].x - eyePoints[3].x, eyePoints[0].y - eyePoints[3].y);

        const ear = (vertical1 + vertical2) / (2 * horizontal || 1);
        return ear;
    }

    async processFrame() {
        if (!this.modelsLoaded || !this.video || this.video.readyState < 2) {
            return;
        }

        let detections = [];
        try {
            detections = await faceapi
                .detectAllFaces(this.video, this.detectorOptions)
                .withFaceLandmarks()
                .withFaceDescriptors();
        } catch (error) {
            console.error(`[${this.attendanceType}] face-api detection error:`, error);
            return;
        }

        if (!detections.length) {
            this.currentDetections = [];
            this.lastResults = [];
            this.previousDetections = [];
            this.updateFPS();
            return;
        }

        const boxes = detections.map(detection => {
            const box = detection.detection.box;
            return {
                start: [box.x * this.scaleX, box.y * this.scaleY],
                end: [(box.x + box.width) * this.scaleX, (box.y + box.height) * this.scaleY]
            };
        });

        const livenessStates = this.evaluateLiveness(detections);

        const now = Date.now();
        const shouldRecognize = now - this.lastRecognitionTime >= this.processIntervalMs;

        let recognitionResults;

        if (shouldRecognize) {
            const liveDescriptors = [];
            const liveIndices = [];

            detections.forEach((det, index) => {
                const liveState = livenessStates[index];
                if (liveState && liveState.status === 'live') {
                    liveDescriptors.push(Array.from(det.descriptor));
                    liveIndices.push(index);
                }
            });

            const recognitionFallback = new Array(detections.length).fill({ matched: false });

            if (liveDescriptors.length) {
                const results = await this.recognizeFaces(liveDescriptors);
                liveIndices.forEach((originalIndex, resultIndex) => {
                    recognitionFallback[originalIndex] = results[resultIndex] || { matched: false };
                });
            }

            recognitionResults = this.normalizeResults(recognitionFallback, boxes.length);
            this.lastResults = recognitionResults;
            this.lastRecognitionTime = now;
        } else {
            recognitionResults = this.normalizeResults(this.lastResults, boxes.length);
            this.lastResults = recognitionResults;
        }

        this.currentDetections = boxes.map((box, index) => {
            const result = recognitionResults[index];
            const liveState = livenessStates[index] || {};
            const matched = result && result.matched;
            let status = matched ? 'matched' : 'unknown';

            if (liveState.status === 'spoof') {
                status = 'spoof';
            } else if (liveState.status === 'liveness_required') {
                status = 'needs_motion';
            }
            return {
                box: box,
                result: result,
                status: status,
                live: liveState
            };
        });

        if (shouldRecognize) {
            for (const detection of this.currentDetections) {
                if (detection.status === 'matched') {
                    await this.autoRecordAttendance(detection.result);
                }
            }
        }

        this.updateFPS();
    }

    async recognizeFaces(faceEmbeddings) {
        if (!faceEmbeddings.length) {
            return [];
        }

        try {
            const response = await fetch('/api/recognize-faces/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ face_embeddings: faceEmbeddings })
            });

            if (!response.ok) {
                console.error(`[${this.attendanceType}] Recognition API error:`, response.status);
                return faceEmbeddings.map(() => ({ matched: false }));
            }

            const data = await response.json();
            if (data && data.success && Array.isArray(data.results)) {
                return data.results;
            }

            return faceEmbeddings.map(() => ({ matched: false }));
        } catch (error) {
            console.error(`[${this.attendanceType}] Error calling recognition API:`, error);
            return faceEmbeddings.map(() => ({ matched: false }));
        }
    }

    normalizeResults(results, expectedLength) {
        if (!Array.isArray(results)) {
            return new Array(expectedLength).fill(null).map(() => ({ matched: false }));
        }

        if (results.length !== expectedLength) {
            const padded = results.slice();
            while (padded.length < expectedLength) {
                padded.push({ matched: false });
            }
            return padded.slice(0, expectedLength);
        }

        return results;
    }

    async autoRecordAttendance(result) {
        const studentId = result && result.student_id;
        if (!studentId) {
            return;
        }

        const now = Date.now();
        if (this.recognitionCooldown.has(studentId)) {
            const last = this.recognitionCooldown.get(studentId);
            if (now - last < this.cooldownMs) {
                return;
            }
        }

        try {
            const response = await fetch('/api/record-attendance/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    student_id: studentId,
                    type: this.attendanceType
                })
            });

            const data = await response.json();
            if (data && data.success) {
                this.recognitionCooldown.set(studentId, now);
                this.addStudentToList(result);
                this.showNotification(data.message || 'Attendance recorded.', 'success');
                this.playSound('success');
            } else {
                console.warn(`[${this.attendanceType}] Attendance recording failed:`, data ? (data.error || data.message) : 'Unknown error');
            }
        } catch (error) {
            console.error(`[${this.attendanceType}] Failed to record attendance:`, error);
        }
    }

    addStudentToList(result) {
        const studentId = result.student_id;
        if (this.recognizedStudents.has(studentId)) {
            return; // Already in list
        }

        this.recognizedStudents.set(studentId, result);

        const listElement = document.getElementById(this.listId);
        const countElement = document.getElementById(this.countId);

        if (listElement) {
            const studentCard = document.createElement('div');
            studentCard.className = 'bg-white dark:bg-gray-800 p-3 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow';
            
            const name = result.name || `${result.first_name || ''} ${result.last_name || ''}`.trim();
            const lrn = result.lrn || result.student_id;
            const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            
            studentCard.innerHTML = `
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <p class="font-semibold text-gray-900 dark:text-white">${name || 'Unknown'}</p>
                        <p class="text-sm text-gray-500 dark:text-gray-400">LRN: ${lrn}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-xs font-medium text-gray-600 dark:text-gray-300">${time}</p>
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                            ✓ Recorded
                        </span>
                    </div>
                </div>
            `;
            
            listElement.insertBefore(studentCard, listElement.firstChild);
        }

        if (countElement) {
            countElement.textContent = this.recognizedStudents.size;
        }
    }

    updateFPS() {
        this.frameCount += 1;
        const now = Date.now();
        const elapsed = now - this.lastFpsUpdate;

        if (elapsed >= 1000) {
            this.fps = Math.round((this.frameCount * 1000) / elapsed);
            this.frameCount = 0;
            this.lastFpsUpdate = now;

            const fpsElement = document.getElementById(this.fpsCounterId);
            if (fpsElement) {
                fpsElement.textContent = this.fps + ' FPS';
                if (this.fps >= 10) {
                    fpsElement.className = 'text-green-500 font-bold';
                } else if (this.fps >= 5) {
                    fpsElement.className = 'text-yellow-500 font-bold';
                } else {
                    fpsElement.className = 'text-red-500 font-bold';
                }
            }
        }
    }

    showNotification(message, type) {
        const toast = document.createElement('div');
        const baseClass = 'fixed top-5 right-5 px-6 py-4 rounded-lg shadow-lg text-white animate-fade-in z-50';
        let variant = 'bg-blue-500';
        if (type === 'success') {
            variant = 'bg-green-500';
        } else if (type === 'error') {
            variant = 'bg-red-500';
        }
        toast.className = baseClass + ' ' + variant;
        toast.textContent = `[${this.attendanceType.toUpperCase()}] ${message || ''}`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    playSound(type) {
        const src = type === 'success' ? '/static/sounds/success.mp3' : '/static/sounds/error.mp3';
        const audio = new Audio(src);
        audio.volume = 0.3;
        audio.play().catch(() => {});
    }

    stop() {
        this.isRunning = false;
        this.currentDetections = [];
        if (this.ctx) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
    }
}

// Initialize BOTH face recognition instances
let timeinFaceRecognition = null;
let timeoutFaceRecognition = null;

document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Hybrid Face Recognition System...');
    
    // TIME IN instance
    timeinFaceRecognition = new HybridFaceRecognition(
        'timein-webcam',           // video ID
        'timein-overlay-canvas',   // canvas ID
        'time_in',                 // attendance type
        'timein-fps-counter',      // FPS counter ID
        'timein-student-list',     // list container ID
        'timein-student-count'     // count display ID
    );
    timeinFaceRecognition.initialize();
    
    // TIME OUT instance
    timeoutFaceRecognition = new HybridFaceRecognition(
        'timeout-webcam',          // video ID
        'timeout-overlay-canvas',  // canvas ID
        'time_out',                // attendance type
        'timeout-fps-counter',     // FPS counter ID
        'timeout-student-list',    // list container ID
        'timeout-student-count'    // count display ID
    );
    timeoutFaceRecognition.initialize();
});

window.addEventListener('beforeunload', () => {
    if (timeinFaceRecognition) {
        timeinFaceRecognition.stop();
    }
    if (timeoutFaceRecognition) {
        timeoutFaceRecognition.stop();
    }
});
