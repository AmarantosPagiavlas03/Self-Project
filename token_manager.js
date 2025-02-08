function getToken() {
    return localStorage.getItem('session_token') || null;
}

// Export for Streamlit component
export default { getToken };