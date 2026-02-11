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

    setText('race-title', data.比赛名称 || '');
    setText('race-group', data.比赛组别 || '');
    setText('race-phase', data.比赛阶段 || '');
    setText('race-progress', data.比赛进度 || '');
    setText('team-id', data.队伍编号 || '---');
    setText('team-name', data.队伍名称 || '---');
    setText('team-members', data.队伍成员 || '---');

    setText('remaining-time', data.剩余时间 || '00:00');
    setText('real-time', data.实时成绩 || '0.000s');
    setText('best-record', data.最好成绩 || '999.999s');
    setText('next-team', data.下支队伍 || '---');

    // Optional: Update colors based on state
    const remainingEl = document.getElementById('remaining-time');
    if (data.剩余时间 && (data.剩余时间 === "00:00" || data.剩余时间.includes("-"))) {
        remainingEl.style.color = "#f56c6c";
    } else {
        remainingEl.style.color = "#f56c6c"; // Default red
    }
};

document.addEventListener('DOMContentLoaded', connectWebSocket);
