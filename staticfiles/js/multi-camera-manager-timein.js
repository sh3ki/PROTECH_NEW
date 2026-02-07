// Multi-Camera Manager for Time In Page
// Manages 1-4 cameras independently

document.addEventListener('DOMContentLoaded', () => {
    const cameraCount = parseInt(document.body.getAttribute('data-camera-count')) || 1;
    
    // Store all camera instances
    const cameras = [];
    
    // Initialize each camera
    for (let i = 1; i <= cameraCount; i++) {
        const suffix = cameraCount === 1 ? '' : `-${i}`;
        const camera = new CameraManager(suffix, i);
        cameras.push(camera);
        camera.init();
    }
    
    // Camera Manager Class - Each instance manages one camera
    function CameraManager(suffix, number) {
        this.suffix = suffix;
        this.number = number;
        this.currentStream = null;
        this.mainStream = null;
        this.activeCameraId = null;
        
        // Get DOM elements
        this.cameraSelect = document.getElementById(`camera-select${suffix}`);
        this.webcamFeed = document.getElementById(`webcam${suffix}`);
        this.cameraPlaceholder = document.getElementById(`camera-placeholder${suffix}`);
        this.statusIndicator = document.getElementById(`status-indicator${suffix}`);
        this.statusDot = document.getElementById(`status-dot${suffix}`);
        this.statusText = document.getElementById(`status-text${suffix}`);
        this.fpsCounter = document.getElementById(`fps-counter${suffix}`);
        this.overlayCanvas = document.getElementById(`overlay-canvas${suffix}`);
        
        // Modal elements (shared for single camera, unique for multi)
        if (cameraCount === 1) {
            this.modal = document.getElementById('camera-test-modal');
            this.closeModal = document.getElementById('close-modal');
            this.cancelCamera = document.getElementById('cancel-camera');
            this.confirmCamera = document.getElementById('confirm-camera');
            this.testVideo = document.getElementById('test-video');
        } else {
            // For multiple cameras, create individual modals
            this.createModal();
        }
        
        this.isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }
    
    CameraManager.prototype.createModal = function() {
        // Create a unique modal for this camera
        const modalId = `camera-test-modal${this.suffix}`;
        const modalHTML = `
            <div id="${modalId}" class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 hidden">
                <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full mx-4 overflow-hidden">
                    <div class="bg-gradient-to-r from-primary to-secondary px-6 py-4 flex justify-between items-center">
                        <h3 class="text-xl font-bold text-white">Test Camera ${this.number}</h3>
                        <button id="close-modal${this.suffix}" class="text-white hover:text-gray-200 transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    <div class="p-6 flex flex-col items-center">
                        <p class="mb-4 text-gray-700 dark:text-gray-300 text-center">
                            Testing camera feed. Make sure the camera is working before confirming.
                        </p>
                        <div class="bg-black rounded-lg overflow-hidden w-full h-96 mb-4 shadow-inner border border-gray-700">
                            <video id="test-video${this.suffix}" autoplay playsinline muted class="w-full h-full object-cover" style="transform: scaleX(-1);"></video>
                        </div>
                        <div class="flex justify-center gap-6 mt-6">
                            <button id="cancel-camera${this.suffix}" class="px-8 py-3 bg-gray-500 hover:bg-gray-600 text-white rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-xl">
                                Cancel
                            </button>
                            <button id="confirm-camera${this.suffix}" class="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 text-white rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-xl flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                                </svg>
                                Confirm & Use Camera
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        this.modal = document.getElementById(modalId);
        this.closeModal = document.getElementById(`close-modal${this.suffix}`);
        this.cancelCamera = document.getElementById(`cancel-camera${this.suffix}`);
        this.confirmCamera = document.getElementById(`confirm-camera${this.suffix}`);
        this.testVideo = document.getElementById(`test-video${this.suffix}`);
    };
    
    CameraManager.prototype.init = function() {
        if (!this.cameraSelect) return;
        
        // Get available cameras
        this.getAvailableCameras();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            this.stopMediaStream(this.currentStream);
            this.stopMediaStream(this.mainStream);
        });
    };
    
    CameraManager.prototype.stopMediaStream = function(stream) {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        return null;
    };
    
    CameraManager.prototype.updateCameraStatus = function(active) {
        if (!this.statusIndicator) return;
        
        if (active) {
            this.statusIndicator.classList.remove('bg-red-400');
            this.statusIndicator.classList.add('bg-green-400');
            this.statusDot.classList.remove('bg-red-500');
            this.statusDot.classList.add('bg-green-500');
            this.statusText.textContent = cameraCount === 1 ? 'Active' : `Cam ${this.number}`;
        } else {
            this.statusIndicator.classList.remove('bg-green-400');
            this.statusIndicator.classList.add('bg-red-400');
            this.statusDot.classList.remove('bg-green-500');
            this.statusDot.classList.add('bg-red-500');
            this.statusText.textContent = cameraCount === 1 ? 'Inactive' : `Cam ${this.number}`;
        }
    };
    
    CameraManager.prototype.getAvailableCameras = async function() {
        try {
            this.cameraSelect.innerHTML = '';
            
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = cameraCount === 1 ? 'Select a camera' : 'Select';
            this.cameraSelect.appendChild(defaultOption);
            
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            stream.getTracks().forEach(track => track.stop());
            
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            videoDevices.forEach((device, index) => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                let label = device.label || `Camera ${index + 1}`;
                
                if (this.isMobileDevice && device.label) {
                    if (/front/i.test(device.label)) {
                        label = `Front Camera`;
                    } else if (/back/i.test(device.label)) {
                        label = `Back Camera`;
                    }
                }
                
                option.textContent = label;
                this.cameraSelect.appendChild(option);
            });
            
            if (videoDevices.length === 0) {
                const option = document.createElement('option');
                option.textContent = 'No cameras found';
                option.disabled = true;
                this.cameraSelect.appendChild(option);
            }
        } catch (error) {
            console.error(`Camera ${this.number} - Error accessing media devices:`, error);
            const errorOption = document.createElement('option');
            errorOption.textContent = 'Error accessing cameras';
            errorOption.disabled = true;
            this.cameraSelect.innerHTML = '';
            this.cameraSelect.appendChild(errorOption);
        }
    };
    
    CameraManager.prototype.createVideoConstraints = function(deviceId) {
        const constraints = {
            video: {
                deviceId: deviceId ? { exact: deviceId } : undefined,
            }
        };
        
        if (this.isMobileDevice) {
            constraints.video.width = { ideal: 720 };
            constraints.video.height = { ideal: 1280 };
            constraints.video.facingMode = { ideal: "user" };
        } else {
            constraints.video.width = { ideal: 1280 };
            constraints.video.height = { ideal: 720 };
        }
        
        return constraints;
    };
    
    CameraManager.prototype.startCameraTest = async function(deviceId) {
        try {
            this.currentStream = this.stopMediaStream(this.currentStream);
            
            const constraints = this.createVideoConstraints(deviceId);
            this.currentStream = await navigator.mediaDevices.getUserMedia(constraints);
            this.testVideo.srcObject = this.currentStream;
            
            this.modal.classList.remove('hidden');
        } catch (error) {
            console.error(`Camera ${this.number} - Error starting camera test:`, error);
            alert(`Failed to access camera ${this.number}. Please try a different camera.`);
            this.cameraSelect.value = '';
        }
    };
    
    CameraManager.prototype.startWebcamFeed = async function(deviceId) {
        try {
            this.mainStream = this.stopMediaStream(this.mainStream);
            
            if (!this.webcamFeed) {
                console.error(`Camera ${this.number} - Webcam video element not found!`);
                return;
            }
            
            if (this.webcamFeed.srcObject) {
                this.webcamFeed.srcObject = null;
            }
            
            const constraints = this.createVideoConstraints(deviceId);
            this.mainStream = await navigator.mediaDevices.getUserMedia(constraints);
            
            this.webcamFeed.srcObject = this.mainStream;
            if (this.cameraPlaceholder) this.cameraPlaceholder.classList.add('hidden');
            
            this.activeCameraId = deviceId;
            this.updateCameraStatus(true);
            
            this.webcamFeed.onplay = () => {
                console.log(`Camera ${this.number} - Main feed playing successfully`);
            };
            
            this.webcamFeed.onerror = (event) => {
                console.error(`Camera ${this.number} - Video element error:`, event);
                this.updateCameraStatus(false);
                this.resetCameraUI();
            };
            
        } catch (error) {
            console.error(`Camera ${this.number} - Error starting webcam feed:`, error);
            alert(`Failed to start camera ${this.number}. Please try again.`);
            this.updateCameraStatus(false);
            this.resetCameraUI();
        }
    };
    
    CameraManager.prototype.resetCameraUI = function() {
        if (this.cameraPlaceholder) this.cameraPlaceholder.classList.remove('hidden');
        this.activeCameraId = null;
        this.updateCameraStatus(false);
    };
    
    CameraManager.prototype.setupEventListeners = function() {
        // Camera selection change
        this.cameraSelect.addEventListener('change', () => {
            const deviceId = this.cameraSelect.value;
            if (deviceId) {
                this.startCameraTest(deviceId);
            } else {
                this.currentStream = this.stopMediaStream(this.currentStream);
                this.mainStream = this.stopMediaStream(this.mainStream);
                this.resetCameraUI();
                this.updateCameraStatus(false);
            }
        });
        
        // Close modal
        const closeTestModal = () => {
            this.currentStream = this.stopMediaStream(this.currentStream);
            this.modal.classList.add('hidden');
            
            if (!this.activeCameraId) {
                this.cameraSelect.value = '';
                this.updateCameraStatus(false);
            }
        };
        
        this.closeModal.addEventListener('click', closeTestModal);
        this.cancelCamera.addEventListener('click', closeTestModal);
        
        // Confirm camera
        this.confirmCamera.addEventListener('click', () => {
            const deviceId = this.cameraSelect.value;
            
            const testTrack = this.currentStream ? this.currentStream.getVideoTracks()[0] : null;
            const cloneTrack = testTrack ? testTrack.clone() : null;
            
            this.currentStream = this.stopMediaStream(this.currentStream);
            this.modal.classList.add('hidden');
            
            setTimeout(() => {
                if (cloneTrack && this.webcamFeed) {
                    try {
                        const newStream = new MediaStream([cloneTrack]);
                        this.webcamFeed.srcObject = newStream;
                        if (this.cameraPlaceholder) this.cameraPlaceholder.classList.add('hidden');
                        this.mainStream = newStream;
                        this.activeCameraId = deviceId;
                        this.updateCameraStatus(true);
                        console.log(`Camera ${this.number} - Successfully reused camera track`);
                        return;
                    } catch (e) {
                        console.warn(`Camera ${this.number} - Failed to reuse track, falling back to new stream:`, e);
                    }
                }
                
                this.startWebcamFeed(deviceId);
            }, 500);
        });
    };
});
