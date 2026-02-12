const connectWebSocket = () => {
    const ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onopen = () => {
        console.log("Connected to server");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateUI(data);
    };

    ws.onclose = () => {
        console.log("Disconnected, retrying in 1s...");
        setTimeout(connectWebSocket, 1000);
    };

    ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        ws.close();
    };
};

const updateUI = (data) => {
    // Helper to safely update text
    const setText = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    };

    const updateTeamMembers = (text) => {
        const container = document.getElementById('team-members');
        if (!container) return;

        // Check if text changed to avoid resetting animation unnecessarily
        if (container.getAttribute('data-text') === text) return;
        container.setAttribute('data-text', text);

        // Reset to measure
        container.textContent = ''; // Clear content
        const span = document.createElement('span');
        span.textContent = text;
        container.appendChild(span);

        // Reset styles to default 'value' class state for measurement
        container.style.overflow = '';
        container.style.whiteSpace = '';
        container.style.display = '';
        span.className = '';
        span.style.animationDuration = '';

        // Check overflow
        // We need to wait a tick for layout? Usually synchronous reflow is forced by offsetWidth
        if (span.offsetWidth > container.clientWidth) {
            // Apply marquee
            span.className = 'marquee-content';
            container.style.overflow = 'hidden';
            container.style.whiteSpace = 'nowrap';
            container.style.display = 'block'; // Ensure block behavior for overflow

            // Adjust animation duration based on length
            // e.g., 50px per second
            const duration = (span.offsetWidth + container.clientWidth) / 50;
            span.style.animationDuration = `${Math.max(5, duration)}s`;
        }
    };

    setText('race-title', data.比赛名称 || '');
    setText('race-group', data.比赛组别 || '');
    setText('race-phase', data.比赛阶段 || '');
    setText('race-progress', data.比赛进度 || '');
    setText('team-id', data.队伍编号 || '---');
    setText('team-name', data.队伍名称 || '等待导入');

    // Use special handler for team members
    updateTeamMembers(data.队伍成员 || '---');

    setText('remaining-time', data.剩余时间 || '00:00');
    setText('real-time', data.实时成绩 || '0.000s');
    setText('best-record', data.最好成绩 || '999.999s');
    setText('next-team', data.下支队伍 || '无');

    // Optional: Update colors based on state
    const remainingEl = document.getElementById('remaining-time');
    if (data.剩余时间 && (data.剩余时间 === "00:00" || data.剩余时间.includes("-"))) {
        remainingEl.style.color = "#f56c6c";
    } else {
        remainingEl.style.color = "#f56c6c"; // Default red
    }
};

document.addEventListener('DOMContentLoaded', connectWebSocket);
