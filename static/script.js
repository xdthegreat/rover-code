function sendCommand(command) {
    fetch('/send_command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: command })
    })
}

document.querySelectorAll('[data-command]').forEach(button => {
    const command = button.getAttribute('data-command');

    button.addEventListener('mousedown', () => {
        button.classList.add('active');
        sendCommand(command);
    });

    const stopHandler = () => {
        button.classList.remove('active');
        sendCommand('stop');
    };

    button.addEventListener('mouseup', stopHandler);
});

const keyToCommand = {
    'w': '.fb_box[data-command="forward"]',
    'a': '.control_box[data-command="left"]',
    's': '.fb_box[data-command="backward"]',
    'd': '.control_box[data-command="right"]', 
};

function activateButton(key) {
    const button = document.querySelector(keyToCommand[key]);
    if (button) {
        button.classList.add('active');
    }
}

function deactivateButton(key) {
    const button = document.querySelector(keyToCommand[key]);
    if (button) {
        button.classList.remove('active');
    }
}

document.addEventListener('keydown', function(event) {
    const key = event.key.toLowerCase();
    if (keyToCommand.hasOwnProperty(key) && !event.repeat) {
        activateButton(key);
        sendCommand({
            'w': 'forward',
            'a': 'left',
            's': 'backward',
            'd': 'right'
        }[key]);
    }
});

document.addEventListener('keyup', function(event) {
    const key = event.key.toLowerCase();
    if (keyToCommand.hasOwnProperty(key)) {
        deactivateButton(key);
        sendCommand('stop')
    }
});

const angleInput = document.getElementById('angle');

angleInput.addEventListener('change', () => {
    const angle = angleInput.value;
    
    fetch('/send_angle', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ angle: angle })
    })
});
