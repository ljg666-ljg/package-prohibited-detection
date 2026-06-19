// PPD System - Camera Real-time Detection
// Captures frames from webcam, sends to server for YOLO detection

let cameraStream = null;
let detectionInterval = null;
let isDetecting = false;
let fpsCounter = 0;
let fpsTimer = null;
let classCounts = {};
let realtimeChart = null;

document.addEventListener('DOMContentLoaded', function () {
    const startBtn = document.getElementById('startCameraBtn');
    const stopBtn = document.getElementById('stopCameraBtn');
    const video = document.getElementById('cameraVideo');
    const canvas = document.getElementById('cameraCanvas');
    const overlay = document.getElementById('overlayCanvas');
    const statusDot = document.getElementById('statusDot');
    const fpsDisplay = document.getElementById('fpsDisplay');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    if (!startBtn) return;

    startBtn.addEventListener('click', async () => {
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'environment' }
            });
            video.srcObject = cameraStream;
            await video.play();

            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            overlay.width = canvas.width;
            overlay.height = canvas.height;

            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusDot.style.display = 'inline-block';
            isDetecting = true;

            // FPS counter
            fpsCounter = 0;
            fpsTimer = setInterval(() => {
                fpsDisplay.textContent = fpsCounter;
                fpsCounter = 0;
            }, 1000);

            // Start detection loop (~5 FPS)
            detectionLoop();
        } catch (err) {
            alert('无法访问摄像头: ' + err.message);
        }
    });

    stopBtn.addEventListener('click', () => {
        stopDetection();
    });

    async function detectionLoop() {
        if (!isDetecting) return;

        // Draw current video frame to canvas
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Send to server for detection
        canvas.toBlob(async (blob) => {
            if (!isDetecting) return;
            const fd = new FormData();
            fd.append('image', blob, 'frame.jpg');
            fd.append('csrfmiddlewaretoken', csrfToken);

            try {
                const res = await fetch('/api/detect/image/', { method: 'POST', body: fd });
                const data = await res.json();
                if (data.success) {
                    fpsCounter++;
                    drawOverlay(data);
                    updateDetections(data);
                }
            } catch (e) {
                // Silently ignore network errors
            }

            if (isDetecting) {
                detectionInterval = setTimeout(detectionLoop, 200); // ~5 FPS
            }
        }, 'image/jpeg', 0.8);
    }

    function drawOverlay(data) {
        const ctx = overlay.getContext('2d');
        ctx.clearRect(0, 0, overlay.width, overlay.height);

        const colors = [
            '#FF3838', '#FF9D97', '#FF701F', '#FFB21D', '#CFD231',
            '#48F90A', '#92CC17', '#3DDB86', '#1A9334', '#00D4BB'
        ];

        // Scale factors
        const scaleX = overlay.width / (video.videoWidth || 640);
        const scaleY = overlay.height / (video.videoHeight || 480);

        if (data.boxes && data.boxes.length > 0) {
            data.boxes.forEach((box, i) => {
                const x1 = box[0] * scaleX, y1 = box[1] * scaleY;
                const x2 = box[2] * scaleX, y2 = box[3] * scaleY;
                const color = colors[data.classes[i] % colors.length];
                const label = (data.class_names_cn[i] || '') + ' ' +
                    (data.confs[i] * 100).toFixed(0) + '%';

                ctx.strokeStyle = color;
                ctx.lineWidth = 2;
                ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

                ctx.fillStyle = color;
                const tw = ctx.measureText(label).width + 8;
                ctx.fillRect(x1, y1 - 20, tw, 18);
                ctx.fillStyle = '#fff';
                ctx.font = '12px "Noto Sans SC"';
                ctx.fillText(label, x1 + 4, y1 - 5);

                // Update class counts
                const cn = data.class_names_cn[i] || 'unknown';
                classCounts[cn] = (classCounts[cn] || 0) + 1;
            });
        }
        updateChart();
    }

    function updateDetections(data) {
        const tbody = document.getElementById('realtimeDetections');
        if (!data.boxes || data.boxes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="2" class="text-center text-success py-2">未检出违禁品</td></tr>';
        } else {
            tbody.innerHTML = data.boxes.map((box, i) => `
                <tr>
                    <td><span class="badge badge-detected">${data.class_names_cn[i]}</span></td>
                    <td style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;">
                        ${(data.confs[i] * 100).toFixed(1)}%
                    </td>
                </tr>
            `).join('');
        }
    }

    function updateChart() {
        const ctx = document.getElementById('realtimeChart');
        if (!ctx) return;
        const labels = Object.keys(classCounts);
        const values = Object.values(classCounts);

        if (realtimeChart) {
            realtimeChart.data.labels = labels;
            realtimeChart.data.datasets[0].data = values;
            realtimeChart.update();
        } else {
            realtimeChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '检出次数', data: values,
                        backgroundColor: 'rgba(0,212,255,0.3)',
                        borderColor: '#00d4ff', borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { labels: { color: '#8892b0' } } },
                    scales: {
                        x: { ticks: { color: '#8892b0' }, grid: { color: 'rgba(0,212,255,0.1)' } },
                        y: { ticks: { color: '#8892b0' }, grid: { color: 'rgba(0,212,255,0.1)' } }
                    }
                }
            });
        }
    }

    function stopDetection() {
        isDetecting = false;
        if (detectionInterval) clearTimeout(detectionInterval);
        if (fpsTimer) clearInterval(fpsTimer);
        if (cameraStream) {
            cameraStream.getTracks().forEach(t => t.stop());
            cameraStream = null;
        }
        document.getElementById('startCameraBtn').disabled = false;
        document.getElementById('stopCameraBtn').disabled = true;
        document.getElementById('statusDot').style.display = 'none';
        document.getElementById('fpsDisplay').textContent = '0';
        document.getElementById('realtimeDetections').innerHTML =
            '<tr><td colspan="2" class="text-center text-muted py-3">摄像头已停止</td></tr>';
        const overlayCtx = document.getElementById('overlayCanvas').getContext('2d');
        overlayCtx.clearRect(0, 0, overlayCtx.canvas.width, overlayCtx.canvas.height);
    }

    // Clean up on page leave
    window.addEventListener('beforeunload', stopDetection);
});
