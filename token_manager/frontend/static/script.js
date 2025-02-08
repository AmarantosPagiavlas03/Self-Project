function getToken() {
    const token = localStorage.getItem('session_token') || '';
    window.parent.postMessage({
        type: 'streamlit:setComponentValue',
        value: token
    }, '*');
}

getToken(); // Call immediately when component loads