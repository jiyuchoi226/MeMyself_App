// Firebase 설정
const firebaseConfig = {
    // Firebase 콘솔에서 가져온 설정을 여기에 넣으세요
    apiKey: "your-api-key",
    authDomain: "your-auth-domain",
    projectId: "your-project-id",
    storageBucket: "your-storage-bucket",
    messagingSenderId: "your-messaging-sender-id",
    appId: "your-app-id"
};

// Firebase 초기화
firebase.initializeApp(firebaseConfig);

// DOM 요소
const googleLoginBtn = document.getElementById('googleLoginBtn');
const logoutBtn = document.getElementById('logoutBtn');
const loginContainer = document.getElementById('loginContainer');
const userInfo = document.getElementById('userInfo');
const userNameSpan = document.getElementById('userName');

// Google 로그인 처리
googleLoginBtn.addEventListener('click', () => {
    const provider = new firebase.auth.GoogleAuthProvider();
    firebase.auth().signInWithPopup(provider)
        .catch(error => {
            console.error('로그인 에러:', error);
        });
});

// 로그아웃 처리
logoutBtn.addEventListener('click', () => {
    firebase.auth().signOut()
        .catch(error => {
            console.error('로그아웃 에러:', error);
        });
});

// 인증 상태 변경 감지
firebase.auth().onAuthStateChanged(user => {
    if (user) {
        // 로그인 상태
        loginContainer.style.display = 'none';
        userInfo.style.display = 'block';
        userNameSpan.textContent = user.displayName;
    } else {
        // 로그아웃 상태
        loginContainer.style.display = 'block';
        userInfo.style.display = 'none';
        userNameSpan.textContent = '';
    }
});

// 간단한 클릭 효과
document.getElementById('loginBtn').addEventListener('click', function() {
    this.style.transform = 'scale(0.95)';
    setTimeout(() => {
        this.style.transform = 'scale(1)';
    }, 100);
}); 