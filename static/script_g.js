// script_g.js 

// --- Global Variable ---
let currentPwmSpeed = 50; 

let currentTiltAngle = 90; 
const TILT_STEP_ANGLE = 5;

let automationModeActive = false; 

// --- Core Function: sendCommand ---
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

// --- Core Function: sendAngle ---
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
    })
    .catch(error => {
        console.error('Error sending angle:', error);
    });
}

// --- Function: sendGlobalSpeed to Backend ---
function sendGlobalSpeed(speed) {
    fetch('/set_global_speed', { // This endpoint needs to be created in app.py
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
    fetch('/send_distance', { // New endpoint needed in app.py
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ distance: distance })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Distance response:', data);
        if (data.status === 'error') {
            alert('Failed to set distance: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error sending distance:', error);
    });
}

function sendDirection(direction) {
    fetch('/send_direction', { // New endpoint needed in app.py
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ direction: direction })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Direction response:', data);
        if (data.status === 'error') {
            alert('Failed to set direction: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error sending direction:', error);
    });
}

function takePhoto() { 
    console.log("Taking photo...");
    fetch('/take_photo', { // New endpoint needed in app.py
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




function fetchEncoderData() {
    fetch('/get_encoder_data') // Call the new Flask endpoint
        .then(response => response.json())
        .then(data => {
            // Update the HTML elements with the received data
            document.getElementById('rpm1').textContent = data.rpm1.toFixed(2);
            document.getElementById('speed1').textContent = data.speed1.toFixed(2);
            document.getElementById('rpm2').textContent = data.rpm2.toFixed(2);
            document.getElementById('speed2').textContent = data.speed2.toFixed(2);
            // console.log('Encoder data received:', data); // Uncomment for debugging
            // Update IMU data

            document.getElementById('imuPitch').textContent = data.pitch.toFixed(2);
            document.getElementById('imuRoll').textContent = data.roll.toFixed(2);
        })
        .catch(error => {
            console.error('Error fetching encoder data:', error);
            // Optionally, display "N/A" or an error message on the dashboard
            document.getElementById('rpm1').textContent = 'N/A';
            document.getElementById('speed1').textContent = 'N/A';
            document.getElementById('rpm2').textContent = 'N/A';
            document.getElementById('speed2').textContent = 'N/A';
            
            document.getElementById('imuPitch').textContent = 'N/A';
            document.getElementById('imuRoll').textContent = 'N/A';
        });
} 

// --- NEW: Function to fetch and display odometry pose data ---
function fetchPoseData() {
    fetch('/get_pose') // Call the new Flask endpoint
        .then(response => response.json())
        .then(data => {
            document.getElementById('poseX').textContent = data.x.toFixed(3);
            document.getElementById('poseY').textContent = data.y.toFixed(3);
            document.getElementById('poseTheta').textContent = data.theta.toFixed(1);
            document.getElementById('absDistance').textContent = data.distance.toFixed(3);
            // console.log('Pose data received:', data); // Uncomment for debugging
        })
        .catch(error => {
            console.error('Error fetching pose data:', error);
            document.getElementById('poseX').textContent = 'N/A';
            document.getElementById('poseY').textContent = 'N/A';
            document.getElementById('poseTheta').textContent = 'N/A';
            
        });
}
function takePhoto() {
    fetch('/take_photo', {method: 'POST'})
        .then(response => response.json())
        .then(data => {
            console.log('Taking photo...', data)
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// --- Get DOM elements ---
const pwmSpeedInput = document.getElementById('pwmSpeedInput');
const setSpeedButton = document.getElementById('setSpeedButton');
const speedUpButton = document.getElementById('speedUpButton');
const speedDownButton = document.getElementById('speedDownButton'); // Corrected variable name
const angleInput = document.getElementById('angle');
const lalaInput = document.getElementById('lala'); 

// NEW: Camera Tilt Control elements
const tiltAngleDisplay = document.getElementById('tiltAngleDisplay');
const tiltUpButton = document.getElementById('tiltUpButton');
const tiltDownButton = document.getElementById('tiltDownButton');
const tiltCenterButton = document.getElementById('tiltCenterButton');

// Automation Control elements
// const distanceRow = document.getElementById('distanceRow'); 
// const distanceInput = document.getElementById('distanceInput');
// const setDistanceButton = document.getElementById('setDistanceButton');
// const directionRow = document.getElementById('directionRow'); 
// const directionInput = document.getElementById('directionInput');
// const setDirectionButton = document.getElementById('setDirectionButton');
// const takePhotoButton = document.getElementById('takePhotoButton');

// --- Initialize input values ---
if (pwmSpeedInput) {
    pwmSpeedInput.value = currentPwmSpeed; 
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

if (speedDownButton) { // This is the corrected variable name
    speedDownButton.addEventListener('click', () => { // Corrected event listener target
        currentPwmSpeed = Math.max(0, currentPwmSpeed - 5); 
        if (pwmSpeedInput) {
            pwmSpeedInput.value = currentPwmSpeed;
        }
        console.log("PWM Speed decreased to:", currentPwmSpeed);
        sendGlobalSpeed(currentPwmSpeed);
    });
}
// --- NEW: Event Listeners for Camera Tilt Control ---
if (tiltUpButton) {
    tiltUpButton.addEventListener('click', () => {
        currentTiltAngle = Math.min(180, currentTiltAngle + TILT_STEP_ANGLE); // Max 180 deg
        if (tiltAngleDisplay) {
            tiltAngleDisplay.textContent = currentTiltAngle;
        }
        console.log("Camera tilt increased to:", currentTiltAngle);
        sendAngle(currentTiltAngle); // Send new tilt angle
    });
}

if (tiltDownButton) {
    tiltDownButton.addEventListener('click', () => {
        currentTiltAngle = Math.max(0, currentTiltAngle - TILT_STEP_ANGLE); // Min 0 deg
        if (tiltAngleDisplay) {
            tiltAngleDisplay.textContent = currentTiltAngle;
        }
        console.log("Camera tilt decreased to:", currentTiltAngle);
        sendAngle(currentTiltAngle); // Send new tilt angle
    });
}

if (tiltCenterButton) {
    tiltCenterButton.addEventListener('click', () => {
        currentTiltAngle = 90; // Set to center (90 degrees)
        if (tiltAngleDisplay) {
            tiltAngleDisplay.textContent = currentTiltAngle;
        }
        console.log("Camera tilt centered at:", currentTiltAngle);
        sendAngle(currentTiltAngle); // Send center angle
    });
}


// --- Event Listeners for Movement Buttons (Mouse & Keyboard) ---

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
        button.classList.add('active');
        if (command !== 'stop') { 
            sendCommand(command); 
        }
    });
// hhh
    const stopHandler = () => {
        button.classList.remove('active');
        sendCommand('stop'); 
        
        // --- NEW: Update UI speed to 0 when STOP is sent ---
        currentPwmSpeed = 0;
        if (pwmSpeedInput) {
            pwmSpeedInput.value = currentPwmSpeed;
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
    if (keyToCommand.hasOwnProperty(key) && !event.repeat) { 
        const command = keyToCommand[key];
        activateButtonVisual(command); 
        sendCommand(command); 
    }
});

document.addEventListener('keyup', function(event) {
    const key = event.key.toLowerCase();
    if (keyToCommand.hasOwnProperty(key)) {
        const command = keyToCommand[key];
        deactivateButtonVisual(command); 
        sendCommand('stop'); 

        // --- NEW: Update UI speed to 0 when keyboard STOP is sent ---
        currentPwmSpeed = 0;
        if (pwmSpeedInput) {
            pwmSpeedInput.value = currentPwmSpeed;
        }
    }
});


// Event listener for "Set Distance" button
if (setDistanceButton) {
    setDistanceButton.addEventListener('click', () => {
        const newDistance = parseInt(distanceInput.value);
        if (!isNaN(newDistance) && newDistance >= 0) {
            currentDistance = newDistance;
            console.log("Distance set to:", currentDistance);
            sendDistance(currentDistance);
        } else {
            alert('Please enter a valid distance.');
            distanceInput.value = currentDistance;
        }
    });
}

if (setDirectionButton) {
    setDirectionButton.addEventListener('click', () => {
        const newDirection = parseInt(directionInput.value);
        if (!isNaN(newDirection) && newDirection >= 0) {
            currentDirection = newDirection;
            console.log("Direction set to:", currentDirection);
            sendDirection(currentDirection);
        } else {
            alert('Please enter a valid direction.');
            directionInput.value = currentDirection;
        }
    });
}

// Function triggered by onclick="onAutomation()" in HTML
function onAutomation() {

    const distanceRow = document.getElementById('distanceRow');
    const directionRow = document.getElementById('directionRow');
    const pwmControlGroup = document.getElementById('pwmControlGroup');
    const tiltControlGroup = document.getElementById('tiltControlGroup');
    const speedControlGroup = document.getElementById('speedControlGroup');
    const motorControlGroup = document.getElementById('motorControlGroup');
    const takePhotoButton = document.getElementById('takePhotoButton');
    const label = document.getElementById('label');

    distanceRow.classList.toggle('hidden');
    directionRow.classList.toggle('hidden');
    pwmControlGroup.classList.toggle('hidden');
    tiltControlGroup.classList.toggle('hidden');
    speedControlGroup.classList.toggle('hidden');
    motorControlGroup.classList.toggle('hidden');
    takePhotoButton.classList.toggle('hidden');
    label.classList.toggle('hidden');

    automationModeActive = !automationModeActive; 
    console.log("Automation Mode Toggled:", automationModeActive);

    if (distanceRow) distanceRow.classList.toggle('hidden', !automationModeActive);
    if (directionRow) directionRow.classList.toggle('hidden', !automationModeActive);

    sendCommand(automationModeActive ? 'start_automation' : 'stop_automation');

    alert(automationModeActive ? "Automation Mode ACTIVATED" : "Automation Mode DEACTIVATED");
}

window.onAutomation = onAutomation;


// NEW: Event listener for "Pose for a pic!" button
if (takePhotoButton) {
    takePhotoButton.addEventListener('click', () => {
        takePhoto(); 
    });
}

// --- Start fetching encoder data periodically ---
setInterval(fetchEncoderData, 200); 
// --- NEW: Start fetching pose data periodically ---
setInterval(fetchPoseData, 200);


// --- Angle Input Listeners ---
if (angleInput) {
    angleInput.addEventListener('change', () => {
        const angle = parseInt(angleInput.value);
        if (!isNaN(angle)) {
            sendAngle(angle);
        }
    });
}

if (lalaInput) {
    lalaInput.addEventListener('change', () => {
        const angle = parseInt(lalaInput.value);
        if (!isNaN(angle)) {
            sendAngle(angle); 
        }
    });
}
setInterval(fetchEncoderData, 200); 