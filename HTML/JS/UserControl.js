var eventX = null;
var eventY = null;
var clickX = null;
var clickY = null;
var refreshInterval = 500;
var intervalId = setInterval(refreshImage, refreshInterval);
var crosshair;
var imgWidth;
var imgHeight;
var displayWidth;
var displayHeight;
var scale;

function returnHome() {
    window.location.href = '/';
}

document.addEventListener('keydown', function(event) {
    if (event.code === 'Space') { // 使用空格键作为触发键
        leftclickMouse();
    }
});

// 当页面加载完成时执行
document.addEventListener('DOMContentLoaded', async function() {
    crosshair = document.getElementById('crosshair');

    // 尝试从localStorage获取Token
    var token = localStorage.getItem('token');

    // 如果Token不存在，重定向到login
    if (!token) {
        window.location.href = 'login';
        return;
    }

    // 向服务器发送请求以验证Token的有效性
    var response = await fetch('/verifytoken', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            token: token
        })
    });

    var result = await response.json();

    // 如果Token无效，重定向到login
    if (!result.valid) {
        window.location.href = 'login';
        return;
    }

    // 如果Token有效，继续加载页面...
});

function imageLoaded() {
    resizeImage();
    if (eventX !== null && eventY !== null) {
        showCrosshair(eventX, eventY);
        eventX = null;
        eventY = null;
    }
}

function resizeImage() {
    var img = document.getElementById('screen_shot');

    // 获取图片的实际大小
    imgWidth = img.naturalWidth;
    imgHeight = img.naturalHeight;

    // 获取浏览器窗口的大小
    // windowWidth = window.innerWidth;
    // windowHeight = window.innerHeight;
    // 获取图片显示区域的可用大小，宽度为屏幕宽度，高度为屏幕高度减去工具栏高度
    var toolbarheight = document.getElementById('toolbar').offsetHeight;
    windowWidth = window.innerWidth;
    windowHeight = window.innerHeight - toolbarheight;

    // 计算缩放因子
    scale = Math.min(windowWidth / imgWidth, windowHeight / imgHeight);

    // 调整图片的大小
    img.style.width = Math.round(imgWidth * scale) + 'px';
    img.style.height = Math.round(imgHeight * scale) + 'px';

    // 更新图片的显示大小
    displayWidth = img.width;
    displayHeight = img.height;
}

function refreshImage() {
    document.getElementById('screen_shot').src = "/get_screen_shot?" + new Date().getTime();
}

function screen_onclick(event) {
    eventX = event.clientX;
    eventY = event.clientY;
    if (this.naturalWidth !== 0 && this.naturalHeight !== 0) {
        showCrosshair(eventX, eventY);
        eventX = null;
        eventY = null;
    }
};

function showCrosshair(x, y) {
    var img = document.getElementById('screen_shot');

    // 获取点击位置相对于图片的坐标
    clickX = x - img.getBoundingClientRect().left;
    clickY = y - img.getBoundingClientRect().top;

    // 根据图片的实际大小和显示大小来调整坐标
    clickX = Math.round(clickX / scale);
    clickY = Math.round(clickY / scale);
    console.log(clickX, clickY);
    
    // 显示十字准星
    crosshair.style.left = x + 'px';
    crosshair.style.top = y + 'px';
    crosshair.style.display = 'block';
}

function adjustInterval(value) {
    document.getElementById('input').value = value;
    refreshInterval = value;
    clearInterval(intervalId);
    intervalId = setInterval(refreshImage, refreshInterval);
}

function confirmInterval() {
    var value = document.getElementById('input').value;
    if (value < 300 || value > 3000) {
        alert("请输入一个在300到3000之间的值");
        return;
    }
    document.getElementById('slider').value = value;
    adjustInterval(value);
}

async function moveMouse() {
    var token = localStorage.getItem('token');
    var response = await fetch('/move_mouse', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': token, // 在请求头中添加token
        },
        body: JSON.stringify({
            x: clickX,
            y: clickY
        })
        }) 
    // 如果状态码为401，说明Token无效，重定向到login
    if (response.status === 401) {
        window.location.href = 'login';
        return;
    }

    var result = await response.json();

    if (result) {
        crosshair.style.border = '2px solid red';
    };
}

async function leftclickMouse() {
    var token = localStorage.getItem('token');
    var response = await fetch('/click_mouse', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': token, // 在请求头中添加token
        },
        body: JSON.stringify({
            opcode: 1
        })
        }) 
    // 如果状态码为401，说明Token无效，重定向到login
    if (response.status === 401) {
        window.location.href = 'login';
        return;
    }

    var result = await response.json();

    if (result) {
        crosshair.style.border = '2px solid red';
    };
}