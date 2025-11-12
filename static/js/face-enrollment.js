// Face Enrollment JavaScript
let selectedStudent = null;
let currentStep = 1; // 1: Front, 2: Left, 3: Right
let capturedImages = {
    front: null,
    left: null,
    right: null
};
let faceEmbeddings = [];
let videoStream = null;
let faceDetectionModel = null;
let detectionInterval = null;

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
    try {
        faceDetectionModel = await blazeface.load();
        console.log('Face detection model loaded');
    } catch (error) {
        console.error('Error loading face detection model:', error);
        showToast('Failed to load face detection model', 'error');
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
    faceEmbeddings = [];
    
    // Reset UI
    updateStepIndicator();
    updateCapturePreview();
    document.getElementById('submit-enrollment-btn').disabled = true;
    
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
    if (!faceDetectionModel) {
        console.error('Face detection model not loaded');
        return;
    }
    
    const video = document.getElementById('camera-video');
    const canvas = document.getElementById('face-detection-canvas');
    const ctx = canvas.getContext('2d');
    
    detectionInterval = setInterval(async () => {
        if (video.readyState === 4) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            const predictions = await faceDetectionModel.estimateFaces(video, false);
            
            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            if (predictions.length > 0) {
                const face = predictions[0];
                
                // Draw face box
                const start = face.topLeft;
                const end = face.bottomRight;
                const size = [end[0] - start[0], end[1] - start[1]];
                
                // Check face pose based on current step
                const isPoseCorrect = checkFacePose(face, currentStep);
                
                ctx.strokeStyle = isPoseCorrect ? '#10B981' : '#EF4444';
                ctx.lineWidth = 3;
                ctx.strokeRect(start[0], start[1], size[0], size[1]);
                
                // Update UI
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
                document.getElementById('capture-btn').disabled = true;
                document.getElementById('face-status').textContent = '⚠ No face detected';
                document.getElementById('face-status').className = 'text-sm mt-2 text-red-400';
            }
        }
    }, 200);
}

function checkFacePose(face, step) {
    // Get face landmarks
    const landmarks = face.landmarks;
    if (!landmarks || landmarks.length < 6) return false;
    
    const leftEye = landmarks[0];
    const rightEye = landmarks[1];
    const nose = landmarks[2];
    
    // Calculate face angle based on eye positions
    const eyeDistance = Math.abs(rightEye[0] - leftEye[0]);
    const noseToLeftEye = Math.abs(nose[0] - leftEye[0]);
    const noseToRightEye = Math.abs(nose[0] - rightEye[0]);
    
    const angleRatio = noseToLeftEye / noseToRightEye;
    
    switch(step) {
        case 1: // Front face - straight ahead
            return angleRatio > 0.85 && angleRatio < 1.15;
        case 2: // Left face - significant tilt (nose much closer to left eye)
            return angleRatio > 1.8 && angleRatio < 3.0;
        case 3: // Right face - significant tilt (nose much closer to right eye)
            return angleRatio > 0.33 && angleRatio < 0.6;
        default:
            return false;
    }
}

function getInstructionForStep(step) {
    switch(step) {
        case 1:
            return 'Look straight at the camera';
        case 2:
            return 'Turn your head to the LEFT (more tilt needed)';
        case 3:
            return 'Turn your head to the RIGHT (more tilt needed)';
        default:
            return 'Position your face in the frame';
    }
}

async function captureImage() {
    const video = document.getElementById('camera-video');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    // Get image data
    const imageData = canvas.toDataURL('image/jpeg', 0.9);
    
    // Generate face embedding (simulated - in production, use actual model)
    const embedding = await generateFaceEmbedding(canvas);
    faceEmbeddings.push(embedding);
    
    // Store captured image
    const stepKey = currentStep === 1 ? 'front' : currentStep === 2 ? 'left' : 'right';
    capturedImages[stepKey] = imageData;
    
    // Update preview
    updateCapturePreview();
    
    // Move to next step
    if (currentStep < 3) {
        currentStep++;
        updateStepIndicator();
        updateInstructions();
        showToast(`Step ${currentStep - 1} completed!`, 'success');
    } else {
        // All steps completed
        stopCamera();
        document.getElementById('submit-enrollment-btn').disabled = false;
        showToast('All faces captured! You can now submit the enrollment.', 'success');
    }
}

async function generateFaceEmbedding(canvas) {
    // This is a placeholder - in production, use actual face embedding model
    // For now, return a simulated 128-dimensional embedding
    const embedding = new Array(128).fill(0).map(() => Math.random());
    return embedding;
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
    
    // Remove from embeddings array
    if (faceEmbeddings.length >= step) {
        faceEmbeddings.splice(step - 1, 1);
    }
    
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

async function submitEnrollment() {
    if (!selectedStudent) {
        showToast('Please select a student first', 'error');
        return;
    }
    
    if (faceEmbeddings.length < 3) {
        showToast('Please capture all three face angles', 'error');
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
