class ForumChat {
    constructor() {
        this.currentUser = null;
        this.currentThread = null;
        this.socket = null;
        this.threads = [];
        this.posts = [];

        this.initializeElements();
        this.bindEvents();
        this.loadThreads();
        this.promptForUsername();
    }

    initializeElements() {
        this.usernameInput = document.getElementById('username-input');
        this.setUsernameBtn = document.getElementById('set-username-btn');
        this.currentUserSpan = document.getElementById('current-user');
        this.newThreadTitle = document.getElementById('new-thread-title');
        this.createThreadBtn = document.getElementById('create-thread-btn');
        this.threadsList = document.getElementById('threads-list');
        this.threadView = document.getElementById('thread-view');
        this.welcomeView = document.getElementById('welcome-view');
        this.threadTitle = document.getElementById('thread-title');
        this.backBtn = document.getElementById('back-btn');
        this.postsContainer = document.getElementById('posts-container');
        this.newPostContent = document.getElementById('new-post-content');
        this.sendPostBtn = document.getElementById('send-post-btn');
    }

    bindEvents() {
        this.setUsernameBtn.addEventListener('click', () => this.setUsername());
        this.usernameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.setUsername();
        });

        this.createThreadBtn.addEventListener('click', () => this.createThread());
        this.newThreadTitle.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.createThread();
        });

        this.backBtn.addEventListener('click', () => this.showWelcomeView());
        this.sendPostBtn.addEventListener('click', () => this.sendPost());
        this.newPostContent.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) this.sendPost();
        });
    }

    promptForUsername() {
        const saved = localStorage.getItem('forum-username');
        if (saved) {
            this.usernameInput.value = saved;
            this.setUsername();
        }
    }

    setUsername() {
        const username = this.usernameInput.value.trim();
        if (!username) {
            alert('Please enter a username');
            return;
        }

        this.currentUser = username;
        localStorage.setItem('forum-username', username);
        
        this.usernameInput.style.display = 'none';
        this.setUsernameBtn.style.display = 'none';
        this.currentUserSpan.textContent = `Logged in as: ${username}`;
        this.currentUserSpan.style.display = 'inline';

        this.initializeSocket();
    }

    initializeSocket() {
        this.socket = io('/chat');
        
        this.socket.on('connect', () => {
            console.log('Connected to chat server');
        });

        this.socket.on('new_post', (post) => {
            if (this.currentThread && post.thread_id === this.currentThread.id) {
                this.addPostToUI(post);
            }
        });

        this.socket.on('status', (data) => {
            this.showStatusMessage(data.msg);
        });
    }

    async loadThreads() {
        try {
            const response = await fetch('/api/threads');
            this.threads = await response.json();
            this.renderThreadsList();
        } catch (error) {
            console.error('Error loading threads:', error);
        }
    }

    renderThreadsList() {
        this.threadsList.innerHTML = '';
        
        this.threads.forEach(thread => {
            const threadElement = document.createElement('div');
            threadElement.className = 'thread-item';
            threadElement.innerHTML = `
                <div class="thread-title">${this.escapeHtml(thread.title)}</div>
                <div style="font-size: 0.8rem; color: #7f8c8d; margin-top: 0.25rem;">
                    Created: ${new Date(thread.created_at).toLocaleDateString()}
                </div>
            `;
            
            threadElement.addEventListener('click', (event) => this.selectThread(thread, event));
            this.threadsList.appendChild(threadElement);
        });
    }

    async createThread() {
        const title = this.newThreadTitle.value.trim();
        if (!title) {
            alert('Please enter a thread title');
            return;
        }

        try {
            const response = await fetch('/api/threads', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title })
            });

            if (response.ok) {
                const newThread = await response.json();
                this.threads.unshift(newThread);
                this.renderThreadsList();
                this.newThreadTitle.value = '';
                this.selectThread(newThread);
            } else {
                const error = await response.json();
                alert(error.error || 'Failed to create thread');
            }
        } catch (error) {
            console.error('Error creating thread:', error);
            alert('Failed to create thread');
        }
    }

    async selectThread(thread, event = null) {
        this.currentThread = thread;
        
        // Update UI
        document.querySelectorAll('.thread-item').forEach(el => el.classList.remove('active'));
        if (event && event.currentTarget) {
            event.currentTarget.classList.add('active');
        }
        
        this.threadTitle.textContent = thread.title;
        this.showThreadView();

        // Join socket room
        if (this.socket) {
            this.socket.emit('join', {
                thread_id: thread.id,
                username: this.currentUser
            });
        }

        // Load posts
        await this.loadPosts(thread.id);
    }

    async loadPosts(threadId) {
        try {
            const response = await fetch(`/api/threads/${threadId}/posts`);
            this.posts = await response.json();
            this.renderPosts();
        } catch (error) {
            console.error('Error loading posts:', error);
        }
    }

    renderPosts() {
        this.postsContainer.innerHTML = '';
        
        this.posts.forEach(post => {
            this.addPostToUI(post);
        });

        this.scrollToBottom();
    }

    addPostToUI(post) {
        const postElement = document.createElement('div');
        postElement.className = 'post';
        postElement.innerHTML = `
            <div class="post-header">
                <span class="post-author">${this.escapeHtml(post.username)}</span>
                <span class="post-time">${new Date(post.created_at).toLocaleString()}</span>
            </div>
            <div class="post-content">${this.escapeHtml(post.content)}</div>
        `;
        
        this.postsContainer.appendChild(postElement);
        this.scrollToBottom();
    }

    async sendPost() {
        if (!this.currentThread || !this.currentUser) return;
        
        const content = this.newPostContent.value.trim();
        if (!content) return;

        try {
            const response = await fetch(`/api/threads/${this.currentThread.id}/posts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: this.currentUser,
                    content: content
                })
            });

            if (response.ok) {
                this.newPostContent.value = '';
            } else {
                const error = await response.json();
                alert(error.error || 'Failed to send message');
            }
        } catch (error) {
            console.error('Error sending post:', error);
            alert('Failed to send message');
        }
    }

    showThreadView() {
        this.welcomeView.style.display = 'none';
        this.threadView.style.display = 'block';
    }

    showWelcomeView() {
        this.threadView.style.display = 'none';
        this.welcomeView.style.display = 'block';
        
        if (this.socket && this.currentThread) {
            this.socket.emit('leave', {
                thread_id: this.currentThread.id,
                username: this.currentUser
            });
        }
        
        this.currentThread = null;
        document.querySelectorAll('.thread-item').forEach(el => el.classList.remove('active'));
    }

    showStatusMessage(message) {
        const statusElement = document.createElement('div');
        statusElement.className = 'status-message';
        statusElement.textContent = message;
        
        this.postsContainer.appendChild(statusElement);
        this.scrollToBottom();
        
        setTimeout(() => {
            statusElement.remove();
        }, 3000);
    }

    scrollToBottom() {
        this.postsContainer.scrollTop = this.postsContainer.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ForumChat();
});