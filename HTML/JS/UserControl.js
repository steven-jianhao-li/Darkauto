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

document.addEventListener('keydown', function (event) {
    if (event.code === 'Space') { // 使用空格键作为触发键
        leftclickMouse();
    }
});

async function setpauseflag(flag){
    // 调用/set_pause_flag接口，设置暂停按钮状态
    var token = localStorage.getItem('token');
    var response = await fetch('/set_pause_flag', {
        method: 'POST',
        headers: {
            'Authorization': token, // 在请求头中添加token
        },
        body: JSON.stringify({
            pause_flag: flag
        })
    });
    // 如果状态码为401，说明Token无效，重定向到login
    if (response.status === 401) {
        window.location.href = 'login';
        return;
    }
    // 返回response的状态码，等待response的结果
    return response.status;
}

async function checkboxinnerclick(){
    let inner = document.getElementById('inner');
    if (inner.classList.contains('active')) {
        // 调用setpauseflag函数，设置暂停按钮状态
        let response = await setpauseflag("False");
        if (response == 200) {
            inner.classList.remove('active');
            return;
        }
        else {
            console.log("Error in setting pause flag, error code: " + response);
        }
    } else {
        // 调用setpauseflag函数，设置暂停按钮状态
        let response = await setpauseflag("True");
        
        if (response == 200) {
            inner.classList.add('active');
            return;
        }
        else {
            console.log("Error in setting pause flag, error code: " + response);
        }
    }
}

// 初始化暂停按钮状态
async function initpauseflag(){
    let inner = document.getElementById('inner');
    // 调用/get_pause_flag接口，初始化暂停按钮状态
    var token = localStorage.getItem('token');
    var response = await fetch('/get_pause_flag', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': token, // 在请求头中添加token
        }
    });
    // 根据返回的结果设置暂停按钮状态
    var result = await response.json();
    console.log(result.pause_flag);
    if (result.pause_flag == true) {
        inner.classList.add('active');
    }
    else if (result.pause_flag == false) {
        inner.classList.remove('active');
    }
}

// 当页面加载完成时执行
document.addEventListener('DOMContentLoaded', async function () {
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
            'Content-Type': 'application/json', // 声明请求体的内容类型为'application/json
            'Authorization': token, // 在请求头中添加token
        }
    });
    var result = await response.json();

    // 如果Token无效，重定向到login
    if (!result.valid) {
        window.location.href = 'login';
        return;
    }

    initpauseflag()
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
    let element = document.getElementById('toolbar');
    let toolbarheight = element.offsetHeight;
    toolbarheight = toolbarheight + 20;
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