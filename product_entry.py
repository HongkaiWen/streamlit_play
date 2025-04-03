import streamlit as st
import streamlit.components.v1 as components

# 定义 HTML 代码实现条形码扫描、拍照和 GPS 定位
html_code = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>移动界面交互</title>
    <script src="https://cdn.jsdelivr.net/npm/@zxing/library@latest"></script>
</head>
<body>
    <button id="scanBarcode">扫描条形码</button>
    <input type="text" id="barcodeResult" readonly>
    <br>
    <input type="file" id="takePhoto" accept="image/*" capture>
    <br>
    <button id="getLocation">获取 GPS 定位</button>
    <input type="text" id="locationResult" readonly>

    <script>
        const barcodeButton = document.getElementById('scanBarcode');
        const barcodeResult = document.getElementById('barcodeResult');
        const photoInput = document.getElementById('takePhoto');
        const locationButton = document.getElementById('getLocation');
        const locationResult = document.getElementById('locationResult');

        // 条形码扫描
        barcodeButton.addEventListener('click', () => {
            const codeReader = new ZXing.BrowserQRCodeReader();
            codeReader.decodeOnceFromVideoDevice(undefined, null)
              .then((result) => {
                    barcodeResult.value = result.text;
                    parent.postMessage({type: 'barcode_scan_result', data: result.text}, '*');
                })
              .catch((err) => {
                    console.error(err);
                });
        });

        // 拍照
        photoInput.addEventListener('change', (event) => {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onloadend = () => {
                    const base64data = reader.result;
                    parent.postMessage({type: 'photo_taken', data: base64data}, '*');
                };
                reader.readAsDataURL(file);
            }
        });

        // 获取 GPS 定位
        locationButton.addEventListener('click', () => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition((position) => {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    locationResult.value = `${latitude}, ${longitude}`;
                    parent.postMessage({type: 'gps_location', data: `${latitude}, ${longitude}`}, '*');
                }, (error) => {
                    console.error(error);
                });
            } else {
                console.error('浏览器不支持地理定位');
            }
        });
    </script>
</body>
</html>
"""

# 嵌入 HTML 代码到 Streamlit 应用
components.html(html_code, height=400)

# 初始化会话状态
if 'barcode' not in st.session_state:
    st.session_state.barcode = ''
if 'photo' not in st.session_state:
    st.session_state.photo = None
if 'location' not in st.session_state:
    st.session_state.location = ''

# 接收来自 HTML 的消息
def on_message_received(message):
    if message['type'] == 'barcode_scan_result':
        st.session_state.barcode = message['data']
    elif message['type'] == 'photo_taken':
        st.session_state.photo = message['data']
    elif message['type'] == 'gps_location':
        st.session_state.location = message['data']

# 模拟接收消息的逻辑（实际需要更完善的实现）
# 这里只是简单示例，在实际中可能需要使用 WebSocket 等进行通信
# 以下代码仅为示意，不能直接运行
# streamlit_socket.on('message', on_message_received)

# 备注输入框
st.text_area("备注", key="remark")

# 显示扫描结果、照片和定位信息
st.write(f"条形码: {st.session_state.barcode}")
if st.session_state.photo:
    st.image(st.session_state.photo)
st.write(f"GPS 定位: {st.session_state.location}")