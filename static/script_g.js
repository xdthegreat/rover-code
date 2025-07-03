// script_g.js 

// --- Global Variable ---
let currentPwmSpeed = 50; 

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
        })
        .catch(error => {
            console.error('Error fetching encoder data:', error);
            // Optionally, display "N/A" or an error message on the dashboard
            document.getElementById('rpm1').textContent = 'N/A';
            document.getElementById('speed1').textContent = 'N/A';
            document.getElementById('rpm2').textContent = 'N/A';
            document.getElementById('speed2').textContent = 'N/A';
        });
}


// --- Get DOM elements ---
const pwmSpeedInput = document.getElementById('pwmSpeedInput');
const setSpeedButton = document.getElementById('setSpeedButton');
const speedUpButton = document.getElementById('speedUpButton');
const speedDownButton = document.getElementById('speedDownButton'); // Corrected variable name
const angleInput = document.getElementById('angle');
const lalaInput = document.getElementById('lala'); 


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