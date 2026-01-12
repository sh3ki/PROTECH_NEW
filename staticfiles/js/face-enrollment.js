// Face Enrollment JavaScript
let selectedStudent = null;
let currentStep = 1; // 1: Front, 2: Left, 3: Right
let capturedImages = {
    front: null,
    left: null,
    right: null
};
let faceEmbeddings = [null, null, null];
let videoStream = null;
let detectionInterval = null;
let latestFaceDetection = null;
let faceApiModelsLoaded = false;
let detectorOptions = null;

const FACE_API_MODEL_URL = window.FACE_API_MODEL_URL || 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.12/model';
const POSE_THRESHOLDS = {
    front: {
        angleMin: 0.7,
        angleMax: 1.4,
        offsetMax: 0.35
    },
    left: {
        angleMin: 0.8,  // Very lenient - accepts any slight left tilt
        offsetMin: 0.05  // Very lenient - accepts minimal offset
    },
    right: {
        angleMax: 1.2,  // Very lenient - accepts any slight right tilt
        offsetMax: -0.05 // Very lenient - accepts minimal offset
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    setupEventListeners();
    loadFaceDetectionModel();
});

function initializePage() {
    updateStats();
}

function updateStats() {
    // Can be enhanced with API call to get real-time stats
}

async function loadFaceDetectionModel() {
    if (faceApiModelsLoaded) {
        return;
    }

    if (typeof faceapi === 'undefined') {
        console.error('face-api.js is not available on window.');
        showToast('Face recognition library failed to load.', 'error');
        return;
    }

    try {
        await Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri(FACE_API_MODEL_URL),
            faceapi.nets.faceLandmark68Net.loadFromUri(FACE_API_MODEL_URL),
            faceapi.nets.faceRecognitionNet.loadFromUri(FACE_API_MODEL_URL)
        ]);
        detectorOptions = new faceapi.TinyFaceDetectorOptions({
            inputSize: 224,
            scoreThreshold: 0.5
        });
        faceApiModelsLoaded = true;
        console.log('face-api models loaded for enrollment.');
    } catch (error) {
        console.error('Error loading face-api models:', error);
        showToast('Failed to load face recognition models', 'error');
    }
}

function setupEventListeners() {
    // Student search
    let searchTimeout;
    document.getElementById('student-search').addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            document.getElementById('search-results').classList.add('hidden');
            return;
        }
        
        document.getElementById('search-spinner').classList.remove('hidden');
        
        searchTimeout = setTimeout(() => {
            searchStudents(query);
        }, 300);
    });

    // Change student button
    document.getElementById('change-student-btn').addEventListener('click', resetStudentSelection);

    // Camera controls
    document.getElementById('start-camera-btn').addEventListener('click', startCamera);
    document.getElementById('capture-btn').addEventListener('click', captureImage);
    
    // Retake buttons
    document.getElementById('retake-front-btn').addEventListener('click', () => retakeImage('front'));
    document.getElementById('retake-left-btn').addEventListener('click', () => retakeImage('left'));
    document.getElementById('retake-right-btn').addEventListener('click', () => retakeImage('right'));

    // Policy modal
    document.getElementById('view-policy-btn').addEventListener('click', openPolicyModal);
    document.getElementById('close-policy-modal').addEventListener('click', closePolicyModal);
    document.getElementById('close-policy-modal-btn').addEventListener('click', closePolicyModal);
    document.getElementById('policy-modal-backdrop').addEventListener('click', closePolicyModal);
    
    // Main policy agreement checkbox
    document.getElementById('policy-agreement').addEventListener('change', checkSubmitEligibility);

    // Submit enrollment
    document.getElementById('submit-enrollment-btn').addEventListener('click', submitEnrollment);

    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        const searchResults = document.getElementById('search-results');
        const searchInput = document.getElementById('student-search');
        if (!searchResults.contains(e.target) && e.target !== searchInput) {
            searchResults.classList.add('hidden');
        }
    });
}

function openPolicyModal() {
    const modal = document.getElementById('policy-modal');
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closePolicyModal() {
    const modal = document.getElementById('policy-modal');
    
    modal.classList.add('hidden');
    document.body.style.overflow = '';
}

async function searchStudents(query) {
    try {
        const response = await fetch(`/registrar/face-enrollment/students/search/?q=${encodeURIComponent(query)}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        });
        
        const data = await response.json();
        document.getElementById('search-spinner').classList.add('hidden');
        
        if (data.status === 'success') {
            displaySearchResults(data.students);
        } else {
            showToast('Error searching students', 'error');
        }
    } catch (error) {
        console.error('Error searching students:', error);
        document.getElementById('search-spinner').classList.add('hidden');
        showToast('Error searching students', 'error');
    }
}

function displaySearchResults(students) {
    const resultsContainer = document.getElementById('search-results');
    
    if (students.length === 0) {
        resultsContainer.innerHTML = `
            <div class="p-4 text-center text-gray-500 dark:text-gray-400">
                No students found
            </div>
        `;
        resultsContainer.classList.remove('hidden');
        return;
    }
    
    let html = '';
    students.forEach(student => {
        const faceStatus = student.has_face_enrolled 
            ? '<span class="text-green-600 dark:text-green-400 text-xs font-medium">✓ Enrolled</span>'
            : '<span class="text-yellow-600 dark:text-yellow-400 text-xs font-medium">Pending</span>';
        
        html += `
            <div class="student-result-item p-4 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-200 dark:border-gray-700 last:border-b-0 transition-colors" 
                 data-student='${JSON.stringify(student)}'>
                <div class="flex items-center space-x-3">
                    <div class="w-12 h-12 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-600 flex-shrink-0">
                        ${student.profile_pic 
                            ? `<img src="${student.profile_pic}" class="w-full h-full object-cover" alt="${student.full_name}">` 
                            : `<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-gray-400 mx-auto mt-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                               </svg>`
                        }
                    </div>
                    <div class="flex-1">
                        <p class="font-semibold text-gray-900 dark:text-white">${student.full_name}</p>
                        <p class="text-sm text-gray-600 dark:text-gray-400">LRN: ${student.lrn}</p>
                        <p class="text-sm text-gray-600 dark:text-gray-400">${student.grade_section}</p>
                    </div>
                    <div class="text-right">
                        ${faceStatus}
                    </div>
                </div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
    resultsContainer.classList.remove('hidden');
    
    // Add click listeners to results
    document.querySelectorAll('.student-result-item').forEach(item => {
        item.addEventListener('click', function() {
            const student = JSON.parse(this.getAttribute('data-student'));
            selectStudent(student);
        });
    });
}

function selectStudent(student) {
    selectedStudent = student;
    
    // Hide search results and empty state
    document.getElementById('search-results').classList.add('hidden');
    document.getElementById('empty-state').classList.add('hidden');
    
    // Show selected student info
    const infoSection = document.getElementById('selected-student-info');
    infoSection.classList.remove('hidden');
    
    // Update student info
    document.getElementById('student-name').textContent = student.full_name;
    document.getElementById('student-lrn').textContent = `LRN: ${student.lrn}`;
    document.getElementById('student-grade-section').textContent = student.grade_section;
    
    // Update profile picture
    const profilePic = document.getElementById('student-profile-pic');
    const profilePlaceholder = document.getElementById('student-profile-placeholder');
    if (student.profile_pic) {
        profilePic.src = student.profile_pic;
        profilePic.classList.remove('hidden');
        profilePlaceholder.classList.add('hidden');
    } else {
        profilePic.classList.add('hidden');
        profilePlaceholder.classList.remove('hidden');
    }
    
    // Update face status
    const statusContainer = document.getElementById('student-face-status');
    if (student.has_face_enrolled) {
        statusContainer.innerHTML = `
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Face Already Enrolled
            </span>
        `;
    } else {
        statusContainer.innerHTML = `
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Pending Enrollment
            </span>
        `;
    }
    
    // Show face capture section
    document.getElementById('face-capture-section').classList.remove('hidden');
    
    // Reset capture state
    resetCaptureState();
}

function resetStudentSelection() {
    selectedStudent = null;
    document.getElementById('selected-student-info').classList.add('hidden');
    document.getElementById('face-capture-section').classList.add('hidden');
    document.getElementById('empty-state').classList.remove('hidden');
    document.getElementById('student-search').value = '';
    stopCamera();
    resetCaptureState();
}

function resetCaptureState() {
    currentStep = 1;
    capturedImages = {
        front: null,
        left: null,
        right: null
    };
    faceEmbeddings = [null, null, null];
    
    // Reset UI
    updateStepIndicator();
    updateCapturePreview();
    document.getElementById('submit-enrollment-btn').disabled = true;
    
    // Reset policy agreement
    const policyCheckbox = document.getElementById('policy-agreement');
    policyCheckbox.checked = false;
    
    // Reset instructions
    document.querySelectorAll('[id^="instruction-"]').forEach(el => {
        el.classList.remove('font-bold');
    });
    document.getElementById('instruction-1').classList.add('font-bold');
}

async function startCamera() {
    try {
        videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            } 
        });
        
        const video = document.getElementById('camera-video');
        video.srcObject = videoStream;
        
        document.getElementById('start-camera-btn').disabled = true;
        
        // Start face detection
        startFaceDetection();
        
        showToast('Camera started successfully', 'success');
    } catch (error) {
        console.error('Error starting camera:', error);
        showToast('Failed to start camera. Please check permissions.', 'error');
    }
}

function stopCamera() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    
    if (detectionInterval) {
        clearInterval(detectionInterval);
        detectionInterval = null;
    }
    
    document.getElementById('start-camera-btn').disabled = false;
    document.getElementById('capture-btn').disabled = true;
}

async function startFaceDetection() {
    if (!faceApiModelsLoaded) {
        await loadFaceDetectionModel();
        if (!faceApiModelsLoaded) {
            return;
        }
    }

    const video = document.getElementById('camera-video');
    const canvas = document.getElementById('face-detection-canvas');
    const ctx = canvas.getContext('2d');

    detectionInterval = setInterval(async () => {
        if (video.readyState !== 4) {
            return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        let detection = null;
        try {
            detection = await faceapi
                .detectSingleFace(video, detectorOptions)
                .withFaceLandmarks()
                .withFaceDescriptor();
        } catch (error) {
            console.error('face-api enrollment detection error:', error);
        }

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (detection && detection.detection) {
            latestFaceDetection = detection;
            const box = detection.detection.box;
            
            // Mirror the box horizontally to match the flipped video
            const mirroredX = canvas.width - box.x - box.width;
            
            const isPoseCorrect = checkFacePose(detection, currentStep);

            ctx.strokeStyle = isPoseCorrect ? '#10B981' : '#EF4444';
            ctx.lineWidth = 3;
            ctx.strokeRect(mirroredX, box.y, box.width, box.height);

            const captureBtn = document.getElementById('capture-btn');
            const faceStatus = document.getElementById('face-status');

            if (isPoseCorrect) {
                captureBtn.disabled = false;
                faceStatus.textContent = '✓ Perfect! Ready to capture';
                faceStatus.className = 'text-sm mt-2 text-green-400 font-semibold';
            } else {
                captureBtn.disabled = true;
                faceStatus.textContent = getInstructionForStep(currentStep);
                faceStatus.className = 'text-sm mt-2 text-yellow-400';
            }
        } else {
            latestFaceDetection = null;
            document.getElementById('capture-btn').disabled = true;
            document.getElementById('face-status').textContent = '⚠ No face detected';
            document.getElementById('face-status').className = 'text-sm mt-2 text-red-400';
        }
    }, 200);
}

function averagePoint(points) {
    if (!points || !points.length) {
        return null;
    }

    const sum = points.reduce((acc, point) => {
        return { x: acc.x + point.x, y: acc.y + point.y };
    }, { x: 0, y: 0 });

    return { x: sum.x / points.length, y: sum.y / points.length };
}

function checkFacePose(detection, step) {
    if (!detection || !detection.landmarks) {
        return false;
    }

    const landmarks = detection.landmarks;
    
    // Get the video element to know its width for mirroring
    const video = document.getElementById('camera-video');
    const videoWidth = video ? video.videoWidth : 0;
    
    // Mirror landmarks horizontally to match the flipped video
    const mirrorPoint = (point) => {
        if (!point || !videoWidth) return point;
        return { x: videoWidth - point.x, y: point.y };
    };
    
    const leftEye = mirrorPoint(averagePoint(landmarks.getLeftEye()));
    const rightEye = mirrorPoint(averagePoint(landmarks.getRightEye()));
    const nosePoints = landmarks.getNose();
    const noseTip = nosePoints && nosePoints.length ? mirrorPoint(nosePoints[nosePoints.length - 1]) : null;

    if (!leftEye || !rightEye || !noseTip) {
        return false;
    }

    const eyeDistance = Math.abs(rightEye.x - leftEye.x);
    if (eyeDistance < 1) {
        return false;
    }

    const noseToLeftEye = Math.abs(noseTip.x - leftEye.x);
    const noseToRightEye = Math.abs(noseTip.x - rightEye.x);
    const epsilon = 1e-6;
    const angleRatio = noseToLeftEye / Math.max(noseToRightEye, epsilon);
    const midX = (leftEye.x + rightEye.x) / 2;
    const normalizedOffset = (noseTip.x - midX) / Math.max(eyeDistance, epsilon); // ~0 front, positive/right tilt, negative/left tilt

    if (typeof window !== 'undefined' && window.DEBUG_FACE_POSE) {
        console.debug('[FacePose]', {
            step,
            angleRatio: Number(angleRatio.toFixed(2)),
            normalizedOffset: Number(normalizedOffset.toFixed(2))
        });
    }

    switch (step) {
        case 1:
            // Front face: LENIENT - accept wide range of "generally forward" poses
            const isFrontAngle = angleRatio >= POSE_THRESHOLDS.front.angleMin && 
                                angleRatio <= POSE_THRESHOLDS.front.angleMax;
            const isFrontOffset = Math.abs(normalizedOffset) <= POSE_THRESHOLDS.front.offsetMax;
            
            // Accept if EITHER condition is good (much more lenient)
            return isFrontAngle || isFrontOffset;
            
        case 2:
            // Left face: VERY LENIENT - accept ANY tilt that's not clearly front-facing
            const isLeftTurn = normalizedOffset >= POSE_THRESHOLDS.left.offsetMin || 
                              angleRatio >= POSE_THRESHOLDS.left.angleMin;
            
            // Only reject if it's clearly front-facing (strict front check)
            const isStrictlyFront = (
                Math.abs(normalizedOffset) <= 0.15 &&
                angleRatio >= 0.9 &&
                angleRatio <= 1
            );
            
            return isLeftTurn && !isStrictlyFront;
            
        case 3:
            // Right face: VERY LENIENT - accept ANY tilt that's not clearly front-facing
            const isRightTurn = normalizedOffset <= POSE_THRESHOLDS.right.offsetMax || 
                               angleRatio <= POSE_THRESHOLDS.right.angleMax;
            
            // Only reject if it's clearly front-facing (strict front check)
            const isStrictlyFrontRight = (
                Math.abs(normalizedOffset) <= 0.15 &&
                angleRatio >= 0.9 &&
                angleRatio <= 1
            );
            
            return isRightTurn && !isStrictlyFrontRight;
            
        default:
            return false;
    }
}

function getInstructionForStep(step) {
    switch(step) {
        case 1:
            return 'Look straight at the camera';
        case 2:
            return 'Turn your head slightly to the LEFT (any tilt is okay)';
        case 3:
            return 'Turn your head slightly to the RIGHT (any tilt is okay)';
        default:
            return 'Position your face in the frame';
    }
}

async function captureImage() {
    if (!latestFaceDetection) {
        showToast('Face not detected. Please position the student in frame.', 'error');
        return;
    }

    if (!latestFaceDetection.descriptor || !latestFaceDetection.descriptor.length) {
        showToast('Unable to read face embedding. Hold still and try again.', 'error');
        return;
    }

    const video = document.getElementById('camera-video');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    const box = latestFaceDetection.detection.box;
    const x1 = box.x;
    const y1 = box.y;
    const x2 = box.x + box.width;
    const y2 = box.y + box.height;
    const maxWidth = video.videoWidth;
    const maxHeight = video.videoHeight;
    const sx = Math.min(Math.max(0, x1), Math.max(0, maxWidth - 1));
    const sy = Math.min(Math.max(0, y1), Math.max(0, maxHeight - 1));
    const ex = Math.min(Math.max(0, x2), maxWidth);
    const ey = Math.min(Math.max(0, y2), maxHeight);
    const width = Math.max(1, ex - sx);
    const height = Math.max(1, ey - sy);

    const faceCanvas = document.createElement('canvas');
    faceCanvas.width = 128;
    faceCanvas.height = 128;
    const faceCtx = faceCanvas.getContext('2d');
    faceCtx.drawImage(
        video,
        sx,
        sy,
        width,
        height,
        0,
        0,
        faceCanvas.width,
        faceCanvas.height
    );
    
    // Get image data
    const imageData = canvas.toDataURL('image/jpeg', 0.9);
    
    const embedding = Array.from(latestFaceDetection.descriptor);
    const embedIndex = Math.max(0, currentStep - 1);
    faceEmbeddings[embedIndex] = embedding;
    
    // Store captured image
    const stepKey = currentStep === 1 ? 'front' : currentStep === 2 ? 'left' : 'right';
    capturedImages[stepKey] = imageData;
    
    // Update preview
    updateCapturePreview();
    
    showToast(`Captured ${stepKey.toUpperCase()} view successfully.`, 'success');

    const nextMissingIndex = faceEmbeddings.findIndex(value => !Array.isArray(value));
    if (nextMissingIndex === -1) {
        // All steps completed
        stopCamera();
        checkSubmitEligibility();
        currentStep = 3;
        updateStepIndicator();
        updateInstructions();
        showToast('All faces captured! Please agree to the policy to submit.', 'success');
        return;
    }

    currentStep = nextMissingIndex + 1;
    updateStepIndicator();
    updateInstructions();
}

function updateCapturePreview() {
    // Update front face
    if (capturedImages.front) {
        document.getElementById('capture-front').src = capturedImages.front;
        document.getElementById('capture-front').classList.remove('hidden');
        document.getElementById('capture-front-placeholder').classList.add('hidden');
        document.getElementById('retake-front-btn').classList.remove('hidden');
    }
    
    // Update left face
    if (capturedImages.left) {
        document.getElementById('capture-left').src = capturedImages.left;
        document.getElementById('capture-left').classList.remove('hidden');
        document.getElementById('capture-left-placeholder').classList.add('hidden');
        document.getElementById('retake-left-btn').classList.remove('hidden');
    }
    
    // Update right face
    if (capturedImages.right) {
        document.getElementById('capture-right').src = capturedImages.right;
        document.getElementById('capture-right').classList.remove('hidden');
        document.getElementById('capture-right-placeholder').classList.add('hidden');
        document.getElementById('retake-right-btn').classList.remove('hidden');
    }
}

function retakeImage(position) {
    // Reset the specific capture
    const stepMap = { 'front': 1, 'left': 2, 'right': 3 };
    const step = stepMap[position];
    
    capturedImages[position] = null;
    
    // Clear embedding slot
    faceEmbeddings[step - 1] = null;
    
    // Set current step to this position
    currentStep = step;
    
    // Update UI
    document.getElementById(`capture-${position}`).classList.add('hidden');
    document.getElementById(`capture-${position}-placeholder`).classList.remove('hidden');
    document.getElementById(`retake-${position}-btn`).classList.add('hidden');
    
    document.getElementById('submit-enrollment-btn').disabled = true;
    
    updateStepIndicator();
    updateInstructions();
    
    // Restart camera if not running
    if (!videoStream) {
        startCamera();
    }
}

function updateStepIndicator() {
    // Update step indicators
    for (let i = 1; i <= 3; i++) {
        const indicator = document.getElementById(`step-${i}-indicator`);
        if (i < currentStep) {
            // Completed
            indicator.className = 'inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-500 dark:bg-green-600 text-white font-bold mb-2';
            indicator.innerHTML = '✓';
        } else if (i === currentStep) {
            // Current
            indicator.className = 'inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary dark:bg-tertiary text-white font-bold mb-2';
            indicator.innerHTML = i;
        } else {
            // Pending
            indicator.className = 'inline-flex items-center justify-center w-12 h-12 rounded-full bg-gray-300 dark:bg-gray-600 text-white font-bold mb-2';
            indicator.innerHTML = i;
        }
    }
    
    // Update progress lines
    document.getElementById('progress-line-1').style.width = currentStep > 1 ? '100%' : '0%';
    document.getElementById('progress-line-2').style.width = currentStep > 2 ? '100%' : '0%';
    
    // Update instruction text
    document.getElementById('face-instruction').textContent = getInstructionForStep(currentStep);
}

function updateInstructions() {
    // Reset all instructions
    document.querySelectorAll('[id^="instruction-"]').forEach(el => {
        el.classList.remove('font-bold');
    });
    
    // Highlight current step
    document.getElementById(`instruction-${currentStep}`).classList.add('font-bold');
}

function checkSubmitEligibility() {
    const allFacesCaptured = faceEmbeddings.every(Array.isArray);
    const policyAgreed = document.getElementById('policy-agreement').checked;
    const submitBtn = document.getElementById('submit-enrollment-btn');
    
    submitBtn.disabled = !(allFacesCaptured && policyAgreed);
}

async function submitEnrollment() {
    if (!selectedStudent) {
        showToast('Please select a student first', 'error');
        return;
    }
    
    if (!faceEmbeddings.every(Array.isArray)) {
        showToast('Please capture all three face angles', 'error');
        return;
    }
    
    if (!document.getElementById('policy-agreement').checked) {
        showToast('Please agree to the school policy before submitting', 'error');
        return;
    }
    
    // Show loading state
    const submitBtn = document.getElementById('submit-enrollment-btn');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
        <svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Processing...
    `;
    
    try {
        const response = await fetch('/registrar/face-enrollment/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                student_id: selectedStudent.id,
                face_embeddings: faceEmbeddings
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast(data.message, 'success');
            
            // Update stats
            updateStats();
            
            // Reset and go back to selection
            setTimeout(() => {
                resetStudentSelection();
            }, 2000);
        } else {
            showToast(data.message || 'Failed to enroll face', 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    } catch (error) {
        console.error('Error submitting enrollment:', error);
        showToast('An error occurred while enrolling face', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// Toast notification function
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('face-enroll-toast-container');
    const toastId = 'toast-' + Date.now();
    
    const bgColors = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'info': 'bg-blue-500',
        'warning': 'bg-yellow-500'
    };
    
    const icons = {
        'success': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />',
        'error': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />',
        'info': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />',
        'warning': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />'
    };
    
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `${bgColors[type]} text-white px-6 py-4 rounded-lg shadow-lg flex items-center space-x-3 transform transition-all duration-300 translate-x-0 opacity-100`;
    toast.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            ${icons[type]}
        </svg>
        <span class="flex-1">${message}</span>
        <button onclick="this.parentElement.remove()" class="text-white hover:text-gray-200">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        </button>
    `;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.transform = 'translateX(400px)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Cleanup when page is unloaded
window.addEventListener('beforeunload', function() {
    stopCamera();
});
