// PPD System - Detection JavaScript (Simplified)
// Single image upload with base64 result display

document.addEventListener('DOMContentLoaded', function () {
    setupUploadPage();
});

function setupUploadPage() {
    var dropZone = document.getElementById('dropZone');
    var fileInput = document.getElementById('fileInput');
    var preview = document.getElementById('preview');
    var previewContainer = document.getElementById('previewContainer');
    var detectBtn = document.getElementById('detectBtn');
    var uploadForm = document.getElementById('uploadForm');
    var confSlider = document.getElementById('confThreshold');
    var iouSlider = document.getElementById('iouThreshold');
    var confValue = document.getElementById('confValue');
    var iouValue = document.getElementById('iouValue');

    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', function () { fileInput.click(); });

    dropZone.addEventListener('dragover', function (e) { e.preventDefault(); dropZone.classList.add('drag-over'); });
    dropZone.addEventListener('dragleave', function () { dropZone.classList.remove('drag-over'); });
    dropZone.addEventListener('drop', function (e) {
        e.preventDefault(); dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) { fileInput.files = e.dataTransfer.files; handleFileSelect(e.dataTransfer.files[0]); }
    });

    fileInput.addEventListener('change', function () {
        if (fileInput.files.length > 0) handleFileSelect(fileInput.files[0]);
    });

    if (confSlider) confSlider.addEventListener('input', function () { confValue.textContent = confSlider.value; });
    if (iouSlider) iouSlider.addEventListener('input', function () { iouValue.textContent = iouSlider.value; });

    function handleFileSelect(file) {
        if (!file.type.startsWith('image/')) { alert('请选择图片文件！'); return; }
        var reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            previewContainer.style.display = 'block';
            detectBtn.disabled = false;
            // Reset results
            document.getElementById('resultImageContainer').style.display = 'none';
            document.getElementById('resultTableBody').innerHTML = '<tr><td colspan="7" class="text-center text-muted py-3">暂无检测数据</td></tr>';
            document.getElementById('resultBadge').style.display = 'none';
            document.getElementById('detectStats').style.display = 'none';
        };
        reader.readAsDataURL(file);
    }

    uploadForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (!fileInput.files.length) return;

        var formData = new FormData();
        formData.append('image', fileInput.files[0]);
        formData.append('conf', confSlider ? confSlider.value : '0.25');
        formData.append('iou', iouSlider ? iouSlider.value : '0.7');
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

        detectBtn.disabled = true;
        detectBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 检测中...';

        try {
            var response = await fetch('/api/detect/image/', { method: 'POST', body: formData });
            var data = await response.json();
            if (data.success) { renderDetectionResult(data); }
            else { alert('检测失败: ' + (data.error || '未知错误')); }
        } catch (err) {
            alert('请求失败: ' + err.message);
        } finally {
            detectBtn.disabled = false;
            detectBtn.innerHTML = '<i class="bi bi-search"></i> 开始检测';
        }
    });
}

function renderDetectionResult(data) {
    var resultContainer = document.getElementById('resultImageContainer');
    var resultArea = document.getElementById('resultArea');

    // Hide placeholder text
    var placeholder = resultArea.querySelector('.text-muted');
    if (placeholder) placeholder.style.display = 'none';

    // Clear container and create result image
    resultContainer.innerHTML = '';
    resultContainer.style.display = 'block';

    // Create a simple img element - much more reliable than canvas
    var resultImg = document.createElement('img');
    resultImg.id = 'resultImg';
    resultImg.style.maxWidth = '100%';
    resultImg.style.borderRadius = '8px';
    resultImg.style.display = 'block';
    resultImg.alt = '检测结果';

    resultImg.src = data.result_image_base64 || data.result_image_url;
    resultContainer.appendChild(resultImg);

    // Badge
    var badge = document.getElementById('resultBadge');
    badge.style.display = 'inline-block';
    if (data.boxes && data.boxes.length > 0) {
        badge.className = 'badge badge-detected';
        badge.textContent = '检出 ' + data.boxes.length + ' 个违禁品';
    } else {
        badge.className = 'badge badge-safe';
        badge.textContent = '未检出违禁品';
    }

    // Stats
    document.getElementById('detectStats').style.display = 'block';
    document.getElementById('inferTime').textContent = data.total_time + 's';
    document.getElementById('objectCount').textContent = data.boxes ? data.boxes.length : 0;
    document.getElementById('deviceInfo').textContent = data.device || 'CPU';

    // Table
    var tbody = document.getElementById('resultTableBody');
    var boxes = data.boxes || [];
    var classNamesCn = data.class_names_cn || [];
    var classNames = data.class_names || [];
    var confs = data.confs || [];
    var boxList = data.boxes || [];

    if (boxList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-success py-3">未检测到违禁物品</td></tr>';
    } else {
        var rows = '';
        for (var i = 0; i < boxList.length; i++) {
            rows += '<tr>' +
                '<td>' + (i + 1) + '</td>' +
                '<td><span class="badge badge-detected">' + (classNamesCn[i] || classNames[i] || '?') + '</span></td>' +
                '<td style="font-family:JetBrains Mono,monospace;">' + (confs[i] * 100).toFixed(2) + '%</td>' +
                '<td>' + boxList[i][0] + '</td><td>' + boxList[i][1] + '</td>' +
                '<td>' + boxList[i][2] + '</td><td>' + boxList[i][3] + '</td>' +
                '</tr>';
        }
        tbody.innerHTML = rows;
    }
}
