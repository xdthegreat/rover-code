// script.js (ALL JAVASCRIPT FOR index.html GOES HERE)

// --- Global Variables ---
let currentPwmSpeed = 50; 
let currentTiltAngle = 90; 
const TILT_STEP_ANGLE = 5; 

let automationModeActive = false; // Flag to track if automation is currently running
let currentDistanceInput = 1.0; // NEW: Default 1 meter
let currentDirectionInput = 0; // NEW: Default 0 degrees


// --- Core Communication Functions ---
function sendCommand(command) {
    fetch('/send_command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: command })
    })
    .then(response => response.json()) 
    .then(data => {
        console.log('Command response:', data);
    })
    .catch(error => {
        console.error('Error sending command:', error);
    });
}

function sendAngle(angle) {
    fetch('/send_angle', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ angle: angle })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Angle response:', data);
        if (data.status === 'error') {
            alert('Failed to set angle: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error sending angle:', error);
    });
}

function sendGlobalSpeed(speed) {
    fetch('/set_global_speed', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ speed: speed })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Global speed set response:', data);
        if (data.status === 'error') {
            alert('Failed to set speed: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error sending global speed:', error);
    });
}

// --- Automation Command Functions ---
function sendDistance(distance) {
    fetch('/send_distance', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ distance: distance })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Distance target response:', data);
        if (data.status === 'error') {
            alert('Failed to set distance: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error sending distance target:', error);
    });
}

function sendDirection(direction) {
    fetch('/send_direction', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ direction: direction })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Direction target response:', data);
        if (data.status === 'error') {
            alert('Failed to set direction: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error sending direction target:', error);
    });
}

function takePhoto() { 
    console.log("Taking photo...");
    fetch('/take_photo', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({}) 
    })
    .then(response => response.json())
    .then(data => {
        console.log('Photo response:', data);
        if (data.status === 'error') {
            alert('Failed to take photo: ' + data.message);
        } else {
            alert('Photo taken!');
        }
    })
    .catch(error => {
        console.error('Error taking photo:', error);
    });
}


// --- Function to fetch and display encoder data ---
function fetchEncoderData() {
    fetch('/get_encoder_data') 
        .then(response => response.json())
        .then(data => {
            document.getElementById('rpm1').textContent = data.rpm1.toFixed(2);
            document.getElementById('speed1').textContent = data.speed1.toFixed(2);
            document.getElementById('rpm2').textContent = data.rpm2.toFixed(2);
            document.getElementById('speed2').textContent = data.speed2.toFixed(2);
            document.getElementById('imuPitch').textContent = data.pitch.toFixed(2); 
            document.getElementById('imuRoll').textContent = data.roll.toFixed(2); 
        })
        .catch(error => { 
            console.error('Error fetching encoder data:', error);
            document.getElementById('rpm1').textContent = 'N/A';
            document.getElementById('speed1').textContent = 'N/A';
            document.getElementById('rpm2').textContent = 'N/A';
            document.getElementById('speed2').textContent = 'N/A';
            document.getElementById('imuPitch').textContent = 'N/A'; 
            document.getElementById('imuRoll').textContent = 'N/A'; 
        });
}

// --- Function to fetch and display odometry pose data ---
function fetchPoseData() {
    fetch('/get_pose') 
        .then(response => response.json())
        .then(data => {
            document.getElementById('poseX').textContent = data.x.toFixed(3);
            document.getElementById('poseY').textContent = data.y.toFixed(3);
            document.getElementById('poseTheta').textContent = data.theta.toFixed(1);
            document.getElementById('absDistance').textContent = data.distance.toFixed(3); 
        })
        .catch(error => {
            console.error('Error fetching pose data:', error);
            document.getElementById('poseX').textContent = 'N/A';
            document.getElementById('poseY').textContent = 'N/A';
            document.getElementById('poseTheta').textContent = 'N/A';
            document.getElementById('absDistance').textContent = 'N/A'; 
        });
}


// --- Get DOM elements (All elements including new automation controls) ---
const pwmSpeedInput = document.getElementById('pwmSpeedInput');
const setSpeedButton = document.getElementById('setSpeedButton');
const speedUpButton = document.getElementById('speedUpButton');
const speedDownButton = document.getElementById('speedDownButton'); 

const tiltAngleDisplay = document.getElementById('tiltAngleDisplay');
const tiltUpButton = document.getElementById('tiltUpButton');
const tiltDownButton = document.getElementById('tiltDownButton');
const tiltCenterButton = document.getElementById('tiltCenterButton');

// Mission Control Input elements
const missionDistanceInput = document.getElementById('missionDistanceInput'); 
const missionDirectionInput = document.getElementById('missionDirectionInput');
// No longer need explicit start/stopMissionButton consts here as onclick is on the Automation button itself.
// const startMissionButton = document.getElementById('startMissionButton');
// const stopMissionButton = document.getElementById('stopMissionButton'); 


// Existing HTML control groups (for hiding/showing)
const pwmControlGroup = document.getElementById('pwmControlGroup');
const tiltControlGroup = document.getElementById('tiltControlGroup');
const speedControlGroup = document.getElementById('speedControlGroup'); 
const motorControlGroup = document.getElementById('motorControlGroup');
const takePhotoButton = document.getElementById('takePhotoButton');
const distanceRow = document.getElementById('distanceRow');
const directionRow = document.getElementById('directionRow');
const run_automation = document.getElementById('run_automation'); // NEW: Automation button

const label = document.getElementById('label'); 


// --- Initialize input values ---
if (pwmSpeedInput) {
    pwmSpeedInput.value = currentPwmSpeed; 
}
if (tiltAngleDisplay) {
    tiltAngleDisplay.textContent = currentTiltAngle;
    sendAngle(currentTiltAngle); // Send default angle to hardware on load
}
if (missionDistanceInput) { // Initialize mission input values
    missionDistanceInput.value = currentDistanceInput;
}
if (missionDirectionInput) { // Initialize mission input values
    missionDirectionInput.value = currentDirectionInput;
}


// --- Event Listeners for Speed Control Buttons ---
if (setSpeedButton) {
    setSpeedButton.addEventListener('click', () => {
        const newSpeed = parseInt(pwmSpeedInput.value);
        if (!isNaN(newSpeed) && newSpeed >= 0 && newSpeed <= 100) {
            currentPwmSpeed = newSpeed;
            console.log("PWM Speed set to:", currentPwmSpeed);
            sendGlobalSpeed(currentPwmSpeed);
        } else {
            alert('Please enter a speed between 0 and 100.');
            pwmSpeedInput.value = currentPwmSpeed;
        }
    });
}

if (speedUpButton) {
    speedUpButton.addEventListener('click', () => {
        currentPwmSpeed = Math.min(100, currentPwmSpeed + 5); 
        if (pwmSpeedInput) {
            pwmSpeedInput.value = currentPwmSpeed;
        }
        console.log("PWM Speed increased to:", currentPwmSpeed);
        sendGlobalSpeed(currentPwmSpeed);
    });
}

if (speedDownButton) { 
    speedDownButton.addEventListener('click', () => { 
        currentPwmSpeed = Math.max(0, currentPwmSpeed - 5); 
        if (pwmSpeedInput) {
            pwmSpeedInput.value = currentPwmSpeed;
        }
        console.log("PWM Speed decreased to:", currentPwmSpeed);
        sendGlobalSpeed(currentPwmSpeed);
    });
}

// --- Event Listeners for Camera Tilt Control ---
if (tiltUpButton) {
    tiltUpButton.addEventListener('click', () => {
        currentTiltAngle = Math.min(180, currentTiltAngle + TILT_STEP_ANGLE); 
        if (tiltAngleDisplay) {
            tiltAngleDisplay.textContent = currentTiltAngle;
        }
        console.log("Camera tilt increased to:", currentTiltAngle);
        sendAngle(currentTiltAngle); 
    });
}

if (tiltDownButton) {
    tiltDownButton.addEventListener('click', () => {
        currentTiltAngle = Math.max(0, currentTiltAngle - TILT_STEP_ANGLE); 
        if (tiltAngleDisplay) {
            tiltAngleDisplay.textContent = currentTiltAngle;
        }
        console.log("Camera tilt decreased to:", currentTiltAngle);
        sendAngle(currentTiltAngle); 
    });
}

if (tiltCenterButton) {
    tiltCenterButton.addEventListener('click', () => {
        currentTiltAngle = 90; 
        if (tiltAngleDisplay) {
            tiltAngleDisplay.textContent = currentTiltAngle;
        }
        console.log("Camera tilt centered at:", currentTiltAngle);
        sendAngle(currentTiltAngle); 
    });
}


// --- Event Listeners for Rover Movement Control Buttons (Mouse & Keyboard) ---

// Map for keyboard commands
const keyToCommand = {
    'w': 'forward',
    'a': 'left',
    's': 'backward',
    'd': 'right', 
};

// Map for finding buttons by command for visual feedback
const commandToButtonSelector = {
    'forward': '.fb_box[data-command="forward"]',
    'left': '.control_box[data-command="left"]',
    'backward': '.fb_box[data-command="backward"]',
    'right': '.control_box[data-command="right"]',
    'stop': '.fb_box[data-command="stop"]' 
};


// Mouse event listeners for directional buttons (mousedown for continuous, mouseup/mouseleave for stop)
document.querySelectorAll('.fb_box[data-command], .control_box[data-command]').forEach(button => {
    const command = button.getAttribute('data-command');

    button.addEventListener('mousedown', () => {
        if (!automationModeActive) { // Check active state inside listener
            button.classList.add('active');
            if (command !== 'stop') { 
                sendCommand(command); 
            }
        } else {
            console.log("Manual mouse command ignored: Automation is active.");
        }
    });

    const stopHandler = () => {
        if (!automationModeActive) { // Check active state inside listener
            button.classList.remove('active');
            sendCommand('stop'); 
            
            currentPwmSpeed = 0;
            if (pwmSpeedInput) {
                pwmSpeedInput.value = currentPwmSpeed;
            }
        }
    };
    button.addEventListener('mouseup', stopHandler);
    button.addEventListener('mouseleave', stopHandler); 
});


// Helper functions for keyboard visual feedback
function activateButtonVisual(command) {
    const selector = commandToButtonSelector[command];
    if (selector) {
        const button = document.querySelector(selector);
        if (button) {
            button.classList.add('active');
        }
    }
}

function deactivateButtonVisual(command) {
    const selector = commandToButtonSelector[command];
    if (selector) {
        const button = document.querySelector(selector);
        if (button) {
            button.classList.remove('active');
        }
    }
}


// Keyboard event listeners (keydown for movement, keyup for stop)
document.addEventListener('keydown', function(event) {
    const key = event.key.toLowerCase();
    if (!automationModeActive && keyToCommand.hasOwnProperty(key) && !event.repeat) { 
        const command = keyToCommand[key];
        activateButtonVisual(command); 
        sendCommand(command); 
    }
    // NEW: Keyboard controls for camera tilt (still allow when automation is active)
    if (event.key === 'q' && tiltUpButton) { 
        event.preventDefault(); 
        tiltUpButton.click(); 
    }
    if (event.key === 'e' && tiltDownButton) { 
        event.preventDefault(); 
        tiltDownButton.click(); 
    }
    if (event.key === 'c' && tiltCenterButton) { 
        event.preventDefault(); 
        tiltCenterButton.click(); 
    }
});

document.addEventListener('keyup', function(event) {
    const key = event.key.toLowerCase();
    if (!automationModeActive && keyToCommand.hasOwnProperty(key)) { 
        const command = keyToCommand[key];
        deactivateButtonVisual(command); 
        sendCommand('stop'); 

        currentPwmSpeed = 0;
        if (pwmSpeedInput) {
            pwmSpeedInput.value = currentPwmSpeed;
        }
    }
});


// --- Automation Control (Logic consolidated here for single button) ---

// This function is triggered by onclick="onAutomation()" from HTML
// It handles both starting and stopping automation based on automationModeActive flag
function onAutomation() {
    // --- NEW: Retrieve values from specific mission input fields ---
    const distance = parseFloat(document.getElementById('distanceInput').value);
    const direction = parseInt(document.getElementById('directionInput').value);

    // Validate inputs
    if (isNaN(distance) || distance < 0) {
        alert('Please enter a valid non-negative distance for the mission.');
        return;
    }
    if (isNaN(direction) || direction < 0 || direction > 360) {
        alert('Please enter a valid direction between 0 and 360 degrees.');
        return;
    }

    // Update global JS variables with current mission targets
    currentMissionDistance = distance;
    currentMissionDirection = direction;

    // Toggle automation mode
    automationModeActive = !automationModeActive; 
    console.log("Automation Mode Toggled:", automationModeActive);

    if (automationModeActive) { // If activating automation
        console.log(`Starting mission with Distance: ${currentMissionDistance}m, Direction: ${currentMissionDirection}°`);
        sendDistance(currentMissionDistance);   // Send targets to backend
        sendDirection(currentMissionDirection); // Send targets to backend
        sendCommand('start_automation');        // Tell backend to start automation
        alert("Automation Mode ACTIVATED. Mission started!");

        // Hide manual controls
        if (pwmControlGroup) pwmControlGroup.classList.add('hidden');
        if (tiltControlGroup) tiltControlGroup.classList.add('hidden');
        if (speedControlGroup) speedControlGroup.classList.add('hidden');
        if (motorControlGroup) motorControlGroup.classList.add('hidden');
        if (takePhotoButton) takePhotoButton.classList.add('hidden');

        if (distanceRow) distanceRow.classList.remove('hidden');
        if (directionRow) directionRow.classList.remove('hidden');
        if (run_automation) run_automation.classList.remove('hidden'); // Hide automation button
        if (label) label.classList.add('hidden'); 

    } else { // If deactivating automation
        sendCommand('stop_automation'); // Tell backend to stop automation
        alert("Automation Mode DEACTIVATED. Mission stopped!");

        // Show manual controls again
        if (pwmControlGroup) pwmControlGroup.classList.remove('hidden');
        if (tiltControlGroup) tiltControlGroup.classList.remove('hidden');
        if (speedControlGroup) speedControlGroup.classList.remove('hidden');
        if (motorControlGroup) motorControlGroup.classList.remove('hidden');
        if (takePhotoButton) takePhotoButton.classList.remove('hidden');

        if (distanceRow) distanceRow.classList.add('hidden');
        if (directionRow) directionRow.classList.add('hidden');
        if (run_automation) run_automation.classList.add('hidden'); // Show automation button
        
        if (label) label.classList.remove('hidden'); 
    }
}

// Attach onAutomation to the window object so it can be called from HTML onclick
window.onAutomation = onAutomation; 


// Event listener for "Pose for a pic!" button (existing)
// const takePhotoButton = document.getElementById('takePhotoButton'); // Redeclared here for the purpose of a proper working code
if (takePhotoButton) {
    takePhotoButton.addEventListener('click', () => {
        takePhoto(); 
    });
}

// --- Start fetching encoder data periodically ---
setInterval(fetchEncoderData, 200); 
// --- Start fetching pose data periodically ---
setInterval(fetchPoseData, 200);