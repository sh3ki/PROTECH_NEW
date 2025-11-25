// Hybrid Camera Manager - Manages TIME IN and TIME OUT cameras simultaneously
// This file contains all the camera management logic for the hybrid attendance page

document.addEventListener('DOMContentLoaded', () => {
    // TIME IN Camera Elements
    const timeinSelect = document.getElementById('timein-camera-select');
    const timeinVideo = document.getElementById('timein-webcam');
    const timeinPlaceholder = document.getElementById('timein-camera-placeholder');
    const timeinModal = document.getElementById('timein-camera-test-modal');
    const timeinTestVideo = document.getElementById('timein-test-video');
    const timeinCloseModal = document.getElementById('timein-close-modal');
    const timeinCancel = document.getElementById('timein-cancel-camera');
    const timeinConfirm = document.getElementById('timein-confirm-camera');
    const timeinIndicator = document.getElementById('timein-status-indicator');
    const timeinDot = document.getElementById('timein-status-dot');
    const timeinText = document.getElementById('timein-status-text');

    // TIME OUT Camera Elements
    const timeoutSelect = document.getElementById('timeout-camera-select');
    const timeoutVideo = document.getElementById('timeout-webcam');
    const timeoutPlaceholder = document.getElementById('timeout-camera-placeholder');
    const timeoutModal = document.getElementById('timeout-camera-test-modal');
    const timeoutTestVideo = document.getElementById('timeout-test-video');
    const timeoutCloseModal = document.getElementById('timeout-close-modal');
    const timeoutCancel = document.getElementById('timeout-cancel-camera');
    const timeoutConfirm = document.getElementById('timeout-confirm-camera');
    const timeoutIndicator = document.getElementById('timeout-status-indicator');
    const timeoutDot = document.getElementById('timeout-status-dot');
    const timeoutText = document.getElementById('timeout-status-text');

    // Stream management
    let timeinStream = null;
    let timeoutStream = null;
    let timeinTestStream = null;
    let timeoutTestStream = null;
    let timeinActive = null;
    let timeoutActive = null;

    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

    // Helper: Stop media stream
    function stopStream(stream) {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        return null;
    }

    // Helper: Update camera status
    function updateStatus(type, active) {
        const indicator = type === 'timein' ? timeinIndicator : timeoutIndicator;
        const dot = type === 'timein' ? timeinDot : timeoutDot;
        const text = type === 'timein' ? timeinText : timeoutText;

        if (active) {
            indicator.classList.remove('bg-red-400');
            indicator.classList.add('bg-green-400');
            dot.classList.remove('bg-red-500');
            dot.classList.add('bg-green-500');
            text.textContent = 'Active';
        } else {
            indicator.classList.remove('bg-green-400');
            indicator.classList.add('bg-red-400');
            dot.classList.remove('bg-green-500');
            dot.classList.add('bg-red-500');
            text.textContent = 'Inactive';
        }
    }

    // Helper: Create video constraints
    function createConstraints(deviceId) {
        const constraints = {
            video: {
                deviceId: deviceId ? { exact: deviceId } : undefined,
            }
        };

        if (isMobile) {
            constraints.video.width = { ideal: 720 };
            constraints.video.height = { ideal: 1280 };
            constraints.video.facingMode = { ideal: "user" };
        } else {
            constraints.video.width = { ideal: 1280 };
            constraints.video.height = { ideal: 720 };
        }

        return constraints;
    }

    // Get available cameras and populate both dropdowns
    async function getCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');

            // Populate TIME IN dropdown
            timeinSelect.innerHTML = '<option value="">Select camera</option>';
            videoDevices.forEach((device, index) => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.textContent = device.label || `Camera ${index + 1}`;
                timeinSelect.appendChild(option);
            });

            // Populate TIME OUT dropdown
            timeoutSelect.innerHTML = '<option value="">Select camera</option>';
            videoDevices.forEach((device, index) => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.textContent = device.label || `Camera ${index + 1}`;
                timeoutSelect.appendChild(option);
            });

            if (videoDevices.length === 0) {
                alert('No cameras found. Please connect a camera and refresh the page.');
            }
        } catch (error) {
            console.error('Error getting cameras:', error);
            alert('Unable to access cameras. Please check permissions.');
        }
    }

    // Start camera test
    async function startCameraTest(deviceId, testVideo) {
        try {
            const constraints = createConstraints(deviceId);
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            testVideo.srcObject = stream;
            return stream;
        } catch (error) {
            console.error('Error starting camera test:', error);
            alert('Failed to access camera. Please try another camera.');
            return null;
        }
    }

    // Start main camera feed
    async function startMainFeed(deviceId, video, placeholder, type) {
        try {
            const constraints = createConstraints(deviceId);
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            
            video.srcObject = stream;
            placeholder.classList.add('hidden');
            updateStatus(type, true);
            
            if (type === 'timein') {
                timeinActive = deviceId;
            } else {
                timeoutActive = deviceId;
            }
            
            return stream;
        } catch (error) {
            console.error('Error starting main feed:', error);
            alert('Failed to start camera feed. Please try again.');
            updateStatus(type, false);
            return null;
        }
    }

    // TIME IN Camera Events
    timeinSelect.addEventListener('change', async () => {
        const deviceId = timeinSelect.value;
        if (deviceId) {
            timeinTestStream = stopStream(timeinTestStream);
            timeinTestStream = await startCameraTest(deviceId, timeinTestVideo);
            if (timeinTestStream) {
                timeinModal.classList.remove('hidden');
            }
        }
    });

    timeinCloseModal.addEventListener('click', () => {
        timeinTestStream = stopStream(timeinTestStream);
        timeinModal.classList.add('hidden');
        if (!timeinActive) timeinSelect.value = '';
    });

    timeinCancel.addEventListener('click', () => {
        timeinTestStream = stopStream(timeinTestStream);
        timeinModal.classList.add('hidden');
        if (!timeinActive) timeinSelect.value = '';
    });

    timeinConfirm.addEventListener('click', async () => {
        const deviceId = timeinSelect.value;
        timeinTestStream = stopStream(timeinTestStream);
        timeinModal.classList.add('hidden');
        
        timeinStream = stopStream(timeinStream);
        timeinStream = await startMainFeed(deviceId, timeinVideo, timeinPlaceholder, 'timein');
    });

    // TIME OUT Camera Events
    timeoutSelect.addEventListener('change', async () => {
        const deviceId = timeoutSelect.value;
        if (deviceId) {
            timeoutTestStream = stopStream(timeoutTestStream);
            timeoutTestStream = await startCameraTest(deviceId, timeoutTestVideo);
            if (timeoutTestStream) {
                timeoutModal.classList.remove('hidden');
            }
        }
    });

    timeoutCloseModal.addEventListener('click', () => {
        timeoutTestStream = stopStream(timeoutTestStream);
        timeoutModal.classList.add('hidden');
        if (!timeoutActive) timeoutSelect.value = '';
    });

    timeoutCancel.addEventListener('click', () => {
        timeoutTestStream = stopStream(timeoutTestStream);
        timeoutModal.classList.add('hidden');
        if (!timeoutActive) timeoutSelect.value = '';
    });

    timeoutConfirm.addEventListener('click', async () => {
        const deviceId = timeoutSelect.value;
        timeoutTestStream = stopStream(timeoutTestStream);
        timeoutModal.classList.add('hidden');
        
        timeoutStream = stopStream(timeoutStream);
        timeoutStream = await startMainFeed(deviceId, timeoutVideo, timeoutPlaceholder, 'timeout');
    });

    // Initialize
    getCameras();

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        stopStream(timeinStream);
        stopStream(timeoutStream);
        stopStream(timeinTestStream);
        stopStream(timeoutTestStream);
    });
});
