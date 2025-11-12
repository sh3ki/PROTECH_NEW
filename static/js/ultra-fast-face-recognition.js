/**
 * Ultra-fast face recognition overlay renderer.
 * Uses BlazeFace for detection and delegates recognition to the backend.
 */

class UltraFastFaceRecognition {
    constructor(attendanceType = 'time_in') {
        this.attendanceType = attendanceType;
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.model = null;
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
        this.processIntervalMs = 500; // throttle recognition to twice per second
        this.lastRecognitionTime = 0;
        this.lastResults = [];
    }

    async initialize() {
        try {
            this.video = document.getElementById('webcam');
            this.canvas = document.getElementById('overlay-canvas');

            if (!this.video || !this.canvas) {
                console.error('Video or canvas element not found.');
                return;
            }

            this.ctx = this.canvas.getContext('2d', { alpha: true });
            if (!this.ctx) {
                console.error('Unable to obtain 2D canvas context.');
                return;
            }

            this.model = await blazeface.load();
            console.log('BlazeFace model loaded.');

            this.registerVideoEvents();

            if (this.video.readyState >= 2 && !this.video.paused && !this.video.ended) {
                this.onVideoReady();
            }
        } catch (error) {
            console.error('Failed to initialise face recognition:', error);
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
            console.log('Face recognition loop started.');
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
                .catch(error => console.error('Error processing frame:', error))
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

    async processFrame() {
        if (!this.model || !this.video || this.video.readyState < 2) {
            return;
        }

        const predictions = await this.model.estimateFaces(this.video, false);

        if (!predictions.length) {
            this.currentDetections = [];
            this.lastResults = [];
            this.updateFPS();
            return;
        }

        const boxes = predictions.map(prediction => {
            const topLeft = prediction.topLeft;
            const bottomRight = prediction.bottomRight;
            return {
                start: [topLeft[0] * this.scaleX, topLeft[1] * this.scaleY],
                end: [bottomRight[0] * this.scaleX, bottomRight[1] * this.scaleY]
            };
        });

        const now = Date.now();
        const shouldRecognize = now - this.lastRecognitionTime >= this.processIntervalMs;

        let recognitionResults;

        if (shouldRecognize) {
            const embeddings = [];
            for (const prediction of predictions) {
                const start = prediction.topLeft;
                const end = prediction.bottomRight;
                const size = [end[0] - start[0], end[1] - start[1]];
                embeddings.push(await this.extractFaceEmbedding(start, size));
            }

            const results = await this.recognizeFaces(embeddings);
            recognitionResults = this.normalizeResults(results, boxes.length);
            this.lastResults = recognitionResults;
            this.lastRecognitionTime = now;
        } else {
            recognitionResults = this.normalizeResults(this.lastResults, boxes.length);
            this.lastResults = recognitionResults;
        }

        this.currentDetections = boxes.map((box, index) => {
            const result = recognitionResults[index];
            const matched = result && result.matched;
            return {
                box: box,
                result: result,
                status: matched ? 'matched' : 'unknown'
            };
        });

        if (shouldRecognize) {
            for (const detection of this.currentDetections) {
                if (detection.status === 'matched') {
                    this.autoRecordAttendance(detection.result).catch(error => {
                        console.error('Failed to record attendance:', error);
                    });
                }
            }
        }

        this.updateFPS();
    }

    async extractFaceEmbedding(start, size) {
    const videoWidth = this.video.videoWidth;
    const videoHeight = this.video.videoHeight;
    const rawX1 = start[0];
    const rawY1 = start[1];
    const rawX2 = rawX1 + size[0];
    const rawY2 = rawY1 + size[1];

    const sx = Math.min(Math.max(0, rawX1), Math.max(0, videoWidth - 1));
    const sy = Math.min(Math.max(0, rawY1), Math.max(0, videoHeight - 1));
    const ex = Math.min(Math.max(0, rawX2), videoWidth);
    const ey = Math.min(Math.max(0, rawY2), videoHeight);
    const width = Math.max(1, ex - sx);
    const height = Math.max(1, ey - sy);

        const faceCanvas = document.createElement('canvas');
        faceCanvas.width = 128;
        faceCanvas.height = 128;
        const faceCtx = faceCanvas.getContext('2d', { willReadFrequently: true });

        faceCtx.drawImage(
            this.video,
            sx,
            sy,
            width,
            height,
            0,
            0,
            faceCanvas.width,
            faceCanvas.height
        );

        const imageData = faceCtx.getImageData(0, 0, faceCanvas.width, faceCanvas.height);
        return this.computeGridEmbedding(imageData.data, faceCanvas.width, faceCanvas.height);
    }

    computeGridEmbedding(pixelData, width, height) {
        const cellsX = 16;
        const cellsY = 8;
        const cellWidth = width / cellsX;
        const cellHeight = height / cellsY;
        const embedding = new Array(cellsX * cellsY).fill(0);

        for (let cy = 0; cy < cellsY; cy++) {
            for (let cx = 0; cx < cellsX; cx++) {
                const startX = Math.floor(cx * cellWidth);
                const endX = Math.max(startX + 1, Math.floor((cx + 1) * cellWidth));
                const startY = Math.floor(cy * cellHeight);
                const endY = Math.max(startY + 1, Math.floor((cy + 1) * cellHeight));

                let sum = 0;
                let count = 0;

                for (let y = startY; y < endY && y < height; y++) {
                    let offset = (y * width + startX) * 4;
                    for (let x = startX; x < endX && x < width; x++) {
                        const r = pixelData[offset];
                        const g = pixelData[offset + 1];
                        const b = pixelData[offset + 2];
                        sum += (r + g + b) / 3;
                        count++;
                        offset += 4;
                    }
                }

                const index = cy * cellsX + cx;
                embedding[index] = count ? (sum / count) / 255 : 0;
            }
        }

        return embedding;
    }

    normalizeResults(results, length) {
        const normalized = [];
        if (!Array.isArray(results)) {
            for (let i = 0; i < length; i++) {
                normalized.push({ matched: false });
            }
            return normalized;
        }

        for (let i = 0; i < length; i++) {
            if (i < results.length && results[i]) {
                normalized.push(results[i]);
            } else {
                normalized.push({ matched: false });
            }
        }

        return normalized;
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
                console.error('Recognition API error:', response.status, await response.text());
                return faceEmbeddings.map(() => ({ matched: false }));
            }

            const data = await response.json();
            if (data && data.success && Array.isArray(data.results)) {
                return data.results;
            }

            return faceEmbeddings.map(() => ({ matched: false }));
        } catch (error) {
            console.error('Error calling recognition API:', error);
            return faceEmbeddings.map(() => ({ matched: false }));
        }
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
                this.showNotification(data.message || 'Attendance recorded.', 'success');
                this.playSound('success');
            } else {
                console.warn('Attendance recording failed:', data ? (data.error || data.message) : 'Unknown error');
            }
        } catch (error) {
            console.error('Failed to record attendance:', error);
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

            const fpsElement = document.getElementById('fps-counter');
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
        toast.textContent = message || '';
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

let faceRecognition = null;

document.addEventListener('DOMContentLoaded', () => {
    const attendanceType = document.body.dataset.attendanceType || 'time_in';
    faceRecognition = new UltraFastFaceRecognition(attendanceType);
    faceRecognition.initialize();
});

window.addEventListener('beforeunload', () => {
    if (faceRecognition) {
        faceRecognition.stop();
    }
});
