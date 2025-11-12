/**
 * Ultra-Fast Face Recognition System
 * Optimized for 10+ FPS with GPU acceleration
 * Compares detected faces against hundreds of student embeddings
 */

class UltraFastFaceRecognition {
    constructor(attendanceType = 'time_in') {
        this.attendanceType = attendanceType; // 'time_in' or 'time_out'
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.model = null;
        this.isRunning = false;
        this.detectedFaces = new Map(); // Store recent detections to avoid duplicates
        this.processingFrame = false;
        this.frameCount = 0;
        this.fps = 0;
        this.lastFpsUpdate = Date.now();
        this.recognitionCooldown = new Map(); // Cooldown per student to avoid spam
        this.cooldownMs = 5000; // 5 seconds between same student recognition
        this.currentDetections = []; // Store current frame detections to continuously draw
    }

    async initialize() {
        console.log('🚀 Initializing Ultra-Fast Face Recognition...');
        
        // Get video and canvas elements
        this.video = document.getElementById('webcam');
        this.canvas = document.getElementById('overlay-canvas');
        
        if (!this.video || !this.canvas) {
            console.error('❌ Video or canvas element not found!');
            return;
        }
        
        this.ctx = this.canvas.getContext('2d', { alpha: true });
        
        console.log('📹 Video element found:', this.video);
        console.log('🎨 Canvas element found:', this.canvas);
        console.log('🎨 Canvas context:', this.ctx);
        console.log('🎨 Canvas computed style:', window.getComputedStyle(this.canvas));
        
        // Wait for video to be ready and sync canvas size
        await this.waitForVideo();
        
        // Load BlazeFace model (ultra-fast face detection)
        console.log('📥 Loading BlazeFace model...');
        this.model = await blazeface.load();
        console.log('✅ BlazeFace model loaded');
        
        // Start recognition loop
        this.isRunning = true;
        this.recognitionLoop();
        
        console.log('✅ Face Recognition System Ready!');
    }
    
    async waitForVideo() {
        return new Promise((resolve) => {
            // Check if video is already playing
            if (this.video.readyState >= 2 && this.video.videoWidth > 0) {
                this.syncCanvasSize();
                console.log('✅ Video already ready');
                resolve();
                return;
            }
            
            // Wait for video to load
            const checkVideo = () => {
                if (this.video.readyState >= 2 && this.video.videoWidth > 0) {
                    this.syncCanvasSize();
                    console.log('✅ Video ready, canvas synced');
                    resolve();
                } else {
                    setTimeout(checkVideo, 100);
                }
            };
            checkVideo();
        });
    }
    
    syncCanvasSize() {
        // Get video parent container for accurate sizing
        const container = this.video.parentElement;
        const rect = container.getBoundingClientRect();
        
        // Set canvas INTERNAL resolution to match video
        this.canvas.width = this.video.videoWidth || 1280;
        this.canvas.height = this.video.videoHeight || 720;
        
        // Set canvas DISPLAY size to match container
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.zIndex = '999';
        
        console.log('📐 Canvas size synced:', {
            canvasWidth: this.canvas.width,
            canvasHeight: this.canvas.height,
            videoWidth: this.video.videoWidth,
            videoHeight: this.video.videoHeight,
            containerWidth: rect.width,
            containerHeight: rect.height,
            canvasStyleWidth: this.canvas.style.width,
            canvasStyleHeight: this.canvas.style.height,
            canvasZIndex: this.canvas.style.zIndex
        });
        
        // Draw a test X across the entire canvas to verify visibility
        this.ctx.strokeStyle = '#FFFF00';
        this.ctx.lineWidth = 5;
        this.ctx.beginPath();
        this.ctx.moveTo(0, 0);
        this.ctx.lineTo(this.canvas.width, this.canvas.height);
        this.ctx.stroke();
        this.ctx.beginPath();
        this.ctx.moveTo(this.canvas.width, 0);
        this.ctx.lineTo(0, this.canvas.height);
        this.ctx.stroke();
        console.log('✅ Drew test X across canvas');
    }

    async recognitionLoop() {
        if (!this.isRunning) return;
        
        // Resync canvas size periodically (in case video size changes)
        if (this.frameCount % 30 === 0) {
            const currentWidth = this.canvas.width;
            const currentHeight = this.canvas.height;
            if (this.video.videoWidth !== currentWidth || this.video.videoHeight !== currentHeight) {
                console.log('📐 Video size changed, resyncing canvas...');
                this.syncCanvasSize();
            }
        }
        
        // Clear canvas and redraw detections every frame
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.redrawDetections();
        
        // Process frame if not already processing
        if (!this.processingFrame) {
            this.processingFrame = true;
            this.processFrame().then(() => {
                this.processingFrame = false;
            }).catch(error => {
                console.error('Error in processFrame:', error);
                this.processingFrame = false;
            });
        }
        
        // Continue loop
        requestAnimationFrame(() => this.recognitionLoop());
    }

    async processFrame() {
        try {
            // Detect faces using BlazeFace
            const predictions = await this.model.estimateFaces(this.video, false);
            
            if (predictions.length === 0) {
                // No faces detected - clear current detections
                this.currentDetections = [];
                return;
            }
            
            // Extract face embeddings for all detected faces
            const faceEmbeddings = [];
            const faceBoundingBoxes = [];
            
            for (const prediction of predictions) {
                const start = prediction.topLeft;
                const end = prediction.bottomRight;
                const size = [end[0] - start[0], end[1] - start[1]];
                
                // Extract face region
                const faceEmbedding = await this.extractFaceEmbedding(start, size);
                faceEmbeddings.push(faceEmbedding);
                faceBoundingBoxes.push({ start, end, size });
            }
            
            // Send embeddings to backend for recognition (batch processing)
            const results = await this.recognizeFaces(faceEmbeddings);
            
            // Store detections for continuous drawing
            this.currentDetections = [];
            for (let i = 0; i < results.length; i++) {
                const result = results[i];
                const box = faceBoundingBoxes[i];
                
                this.currentDetections.push({
                    box: box,
                    result: result,
                    isMatched: result.matched
                });
                
                if (result.matched) {
                    // Auto-record attendance if not in cooldown
                    this.autoRecordAttendance(result);
                }
            }
            
            // Update FPS counter
            this.updateFPS();
            
        } catch (error) {
            console.error('Error in processFrame:', error);
        }
    }
    
    redrawDetections() {
        // Continuously draw stored detections every frame
        if (this.currentDetections.length > 0) {
            console.log(`🔄 Redrawing ${this.currentDetections.length} detection(s)`);
        }
        
        for (const detection of this.currentDetections) {
            this.drawBoundingBox(detection.box, detection.result, detection.isMatched);
        }
        
        // Also draw a persistent test square to verify canvas is working
        this.ctx.strokeStyle = '#FF00FF';
        this.ctx.lineWidth = 5;
        this.ctx.strokeRect(100, 100, 100, 100);
    }

    async extractFaceEmbedding(start, size) {
        /**
         * Extract face embedding from video frame
         * This creates a simplified embedding based on face region
         * In production, use FaceNet or similar for real embeddings
         */
        const [x, y] = start;
        const [width, height] = size;
        
        // Create temporary canvas for face extraction
        const faceCanvas = document.createElement('canvas');
        faceCanvas.width = 128;
        faceCanvas.height = 128;
        const faceCtx = faceCanvas.getContext('2d');
        
        // Draw face region (resized to 128x128)
        faceCtx.drawImage(
            this.video,
            x, y, width, height,
            0, 0, 128, 128
        );
        
        // Get image data
        const imageData = faceCtx.getImageData(0, 0, 128, 128);
        const data = imageData.data;
        
        // Create simplified embedding (128 dimensions)
        // This is a placeholder - use FaceNet for real embeddings
        const embedding = new Array(128);
        for (let i = 0; i < 128; i++) {
            const idx = i * 4 * 128; // Sample pixels
            embedding[i] = (data[idx] + data[idx + 1] + data[idx + 2]) / (3 * 255);
        }
        
        return embedding;
    }

    async recognizeFaces(faceEmbeddings) {
        /**
         * Send face embeddings to backend for recognition
         * Backend compares against all student embeddings in parallel
         */
        try {
            const response = await fetch('/api/recognize-faces/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    face_embeddings: faceEmbeddings
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                return data.results;
            } else {
                console.error('Recognition failed:', data.error);
                return faceEmbeddings.map(() => ({ matched: false }));
            }
        } catch (error) {
            console.error('Error in recognizeFaces:', error);
            return faceEmbeddings.map(() => ({ matched: false }));
        }
    }

    drawBoundingBox(box, result, isMatched) {
        const { start, end } = box;
        let [x1, y1] = start;
        let [x2, y2] = end;
        
        // Ensure coordinates are within canvas bounds
        x1 = Math.max(0, Math.min(x1, this.canvas.width));
        y1 = Math.max(0, Math.min(y1, this.canvas.height));
        x2 = Math.max(0, Math.min(x2, this.canvas.width));
        y2 = Math.max(0, Math.min(y2, this.canvas.height));
        
        const width = x2 - x1;
        const height = y2 - y1;
        
        // Set colors - BRIGHT AND SOLID
        const color = isMatched ? '#00FF00' : '#FF0000'; // Green or Red
        const fillColor = isMatched ? 'rgba(0, 255, 0, 0.3)' : 'rgba(255, 0, 0, 0.3)';
        
        console.log(`🎨 DRAWING ${isMatched ? '✅ GREEN' : '❌ RED'} BOX at [${x1.toFixed(0)}, ${y1.toFixed(0)}] to [${x2.toFixed(0)}, ${y2.toFixed(0)}]`);
        console.log(`   Canvas context exists: ${!!this.ctx}, Canvas size: ${this.canvas.width}x${this.canvas.height}`);
        
        // Draw SOLID fill FIRST
        this.ctx.fillStyle = fillColor;
        this.ctx.fillRect(x1, y1, width, height);
        console.log(`   ✓ Drew fill rect`);
        
        
        // Draw THICK rectangle border
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 15;
        this.ctx.strokeRect(x1, y1, width, height);
        console.log(`   ✓ Drew border stroke`);
        
        // Draw corner markers for MAXIMUM visibility
        const cornerSize = 40;
        this.ctx.lineWidth = 15;
        // Top-left corner
        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1 + cornerSize);
        this.ctx.lineTo(x1, y1);
        this.ctx.lineTo(x1 + cornerSize, y1);
        this.ctx.stroke();
        // Top-right corner
        this.ctx.beginPath();
        this.ctx.moveTo(x2 - cornerSize, y1);
        this.ctx.lineTo(x2, y1);
        this.ctx.lineTo(x2, y1 + cornerSize);
        this.ctx.stroke();
        // Bottom-left corner
        this.ctx.beginPath();
        this.ctx.moveTo(x1, y2 - cornerSize);
        this.ctx.lineTo(x1, y2);
        this.ctx.lineTo(x1 + cornerSize, y2);
        this.ctx.stroke();
        // Bottom-right corner
        this.ctx.beginPath();
        this.ctx.moveTo(x2 - cornerSize, y2);
        this.ctx.lineTo(x2, y2);
        this.ctx.lineTo(x2, y2 - cornerSize);
        this.ctx.stroke();
        
        // Draw background for text
        const textBgHeight = 40;
        this.ctx.fillStyle = isMatched ? 'rgba(0, 255, 0, 0.9)' : 'rgba(255, 0, 0, 0.9)';
        this.ctx.fillRect(x1, y1 - textBgHeight, width, textBgHeight);
        
        // Draw text
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 20px Arial';
        
        if (isMatched) {
            const text = result.lrn ? `LRN: ${result.lrn}` : `ID: ${result.student_id}`;
            this.ctx.fillText(text, x1 + 10, y1 - 15);
            
            // Draw confidence if matched
            if (result.confidence) {
                this.ctx.font = 'bold 16px Arial';
                const confText = `${(result.confidence * 100).toFixed(1)}%`;
                const confWidth = this.ctx.measureText(confText).width;
                this.ctx.fillText(confText, x2 - confWidth - 10, y1 - 15);
            }
        } else {
            this.ctx.fillText('UNAUTHORIZED', x1 + 10, y1 - 15);
        }
    }

    async autoRecordAttendance(result) {
        /**
         * Automatically record attendance when student is recognized
         * Uses cooldown to prevent duplicate recordings
         */
        const studentId = result.student_id;
        const now = Date.now();
        
        // Check cooldown
        if (this.recognitionCooldown.has(studentId)) {
            const lastRecording = this.recognitionCooldown.get(studentId);
            if (now - lastRecording < this.cooldownMs) {
                return; // Still in cooldown
            }
        }
        
        // Record attendance
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
            
            if (data.success) {
                // Set cooldown
                this.recognitionCooldown.set(studentId, now);
                
                // Show success notification
                this.showNotification(data.message, 'success');
                
                // Play success sound
                this.playSound('success');
            } else {
                console.log('Attendance recording failed:', data.message);
            }
        } catch (error) {
            console.error('Error recording attendance:', error);
        }
    }

    updateFPS() {
        this.frameCount++;
        const now = Date.now();
        const elapsed = now - this.lastFpsUpdate;
        
        if (elapsed >= 1000) {
            this.fps = Math.round(this.frameCount * 1000 / elapsed);
            this.frameCount = 0;
            this.lastFpsUpdate = now;
            
            // Update FPS display
            const fpsElement = document.getElementById('fps-counter');
            if (fpsElement) {
                fpsElement.textContent = `${this.fps} FPS`;
                
                // Color code based on performance
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

    showNotification(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `fixed top-5 right-5 px-6 py-4 rounded-lg shadow-lg text-white ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 'bg-blue-500'
        } animate-fade-in z-50`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    playSound(type) {
        // Play sound effect
        const audio = new Audio(type === 'success' ? '/static/sounds/success.mp3' : '/static/sounds/error.mp3');
        audio.volume = 0.3;
        audio.play().catch(() => {
            // Ignore if sound fails
        });
    }

    stop() {
        console.log('🛑 Stopping face recognition...');
        this.isRunning = false;
        // Don't stop the video stream - it's managed by the page
    }
}

// Global instance
let faceRecognition = null;

// Initialize when page loads - delay to ensure video is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌐 DOM loaded, waiting for video to be ready...');
    
    // Wait a bit for the page's webcam to initialize
    setTimeout(() => {
        const attendanceType = document.body.dataset.attendanceType || 'time_in';
        faceRecognition = new UltraFastFaceRecognition(attendanceType);
        faceRecognition.initialize().catch(error => {
            console.error('❌ Failed to initialize face recognition:', error);
        });
    }, 1000);
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (faceRecognition) {
        faceRecognition.stop();
    }
});
