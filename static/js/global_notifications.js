// CalmSphere Global Notifications & Reminders System

// Inject CSS styles for Toasts and Dropdowns dynamically
(function injectStyles() {
    const css = `
        /* Toast Alert Styling */
        #toast-container {
            position: fixed;
            top: 24px;
            right: 24px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-width: 360px;
            width: calc(100vw - 48px);
            pointer-events: none;
        }

        .cs-toast {
            background: rgba(255, 254, 250, 0.88);
            backdrop-filter: blur(12px) saturate(180%);
            -webkit-backdrop-filter: blur(12px) saturate(180%);
            border: 1px solid rgba(191, 139, 88, 0.25);
            box-shadow: 0 16px 36px rgba(75, 54, 37, 0.12);
            border-radius: 18px;
            padding: 16px 20px;
            display: flex;
            align-items: flex-start;
            gap: 14px;
            color: #4f3f2f;
            pointer-events: auto;
            transform: translateX(120%);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
        }

        .cs-toast.show {
            transform: translateX(0);
            opacity: 1;
        }

        .cs-toast-icon {
            font-size: 1.5rem;
            line-height: 1;
            padding: 8px;
            background: rgba(191, 139, 88, 0.12);
            border-radius: 12px;
        }

        .cs-toast-body {
            flex-grow: 1;
        }

        .cs-toast-title {
            font-weight: 700;
            font-size: 0.95rem;
            color: #7a5235;
            margin-bottom: 2px;
        }

        .cs-toast-desc {
            font-size: 0.85rem;
            line-height: 1.4;
            color: #6a5a4c;
        }

        /* Bell Notification Dropdown Wrapper */
        .bell-wrapper {
            position: relative;
            display: inline-block;
        }

        #bell-btn {
            position: relative;
        }

        #bell-badge {
            position: absolute;
            top: -4px;
            right: -4px;
            background: #e84a4a;
            color: white;
            font-size: 10px;
            font-weight: 700;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #ffffff;
            box-shadow: 0 4px 10px rgba(232, 74, 74, 0.3);
            transition: all 0.3s;
        }

        /* Notification Dropdown Panel */
        #notification-dropdown {
            position: absolute;
            top: calc(100% + 12px);
            right: 0;
            width: 380px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(191, 139, 88, 0.2);
            border-radius: 24px;
            box-shadow: 0 24px 50px rgba(75, 54, 37, 0.15);
            overflow: hidden;
            display: none;
            flex-direction: column;
            z-index: 1000;
            opacity: 0;
            transform: translateY(10px);
            transition: opacity 0.25s, transform 0.25s;
        }

        #notification-dropdown.active {
            display: flex;
            opacity: 1;
            transform: translateY(0);
        }

        .nd-header {
            padding: 16px 20px;
            border-bottom: 1px solid rgba(191, 139, 88, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(191, 139, 88, 0.05);
        }

        .nd-title {
            font-weight: 700;
            color: #5a3f27;
            margin: 0;
            font-size: 1.05rem;
        }

        .nd-clear-btn {
            background: none;
            border: none;
            color: #bf8b58;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 8px;
            transition: background 0.2s;
        }

        .nd-clear-btn:hover {
            background: rgba(191, 139, 88, 0.1);
        }

        .nd-list {
            max-height: 320px;
            overflow-y: auto;
        }

        .nd-item {
            padding: 14px 20px;
            border-bottom: 1px solid rgba(191, 139, 88, 0.06);
            display: flex;
            gap: 12px;
            transition: background 0.2s;
            cursor: pointer;
            position: relative;
        }

        .nd-item:hover {
            background: rgba(191, 139, 88, 0.03);
        }

        .nd-item.unread {
            background: rgba(191, 139, 88, 0.05);
        }

        .nd-item-icon {
            font-size: 1.3rem;
            padding: 6px;
            background: rgba(191, 139, 88, 0.08);
            border-radius: 10px;
            align-self: flex-start;
        }

        .nd-item-content {
            flex-grow: 1;
        }

        .nd-item-msg {
            font-size: 0.88rem;
            line-height: 1.4;
            color: #4f3f2f;
            margin-bottom: 4px;
        }

        .nd-item-time {
            font-size: 0.76rem;
            color: #9a8a7c;
        }

        .nd-item-delete {
            opacity: 0;
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            border: none;
            background: rgba(232, 74, 74, 0.1);
            color: #e84a4a;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 12px;
        }

        .nd-item:hover .nd-item-delete {
            opacity: 1;
        }

        .nd-item-delete:hover {
            background: #e84a4a;
            color: white;
        }

        .nd-empty {
            padding: 30px 20px;
            text-align: center;
            color: #9a8a7c;
            font-size: 0.9rem;
        }

        /* Screen pop indicator animation */
        @keyframes pulseDot {
            0% { transform: scale(0.9); opacity: 0.8; }
            50% { transform: scale(1.1); opacity: 1; }
            100% { transform: scale(0.9); opacity: 0.8; }
        }
    `;
    const styleNode = document.createElement('style');
    styleNode.innerHTML = css;
    document.head.appendChild(styleNode);
})();

// Notifications Data Layer
const CS_Notifications = {
    getAll() {
        try {
            return JSON.parse(localStorage.getItem('calmsphere_notifications') || '[]');
        } catch (e) {
            return [];
        }
    },

    save(list) {
        localStorage.setItem('calmsphere_notifications', JSON.stringify(list));
    },

    add(emoji, title, message, actionUrl = null) {
        const list = this.getAll();
        const item = {
            id: Date.now() + Math.random().toString(36).substr(2, 9),
            emoji,
            title,
            message,
            timestamp: Date.now(),
            read: false,
            actionUrl
        };
        list.unshift(item);
        this.save(list);

        // Render screen Toast
        this.showToast(item);

        // Update Bell dropdown
        this.renderDropdown();
        this.updateBadge();
        return item;
    },

    markAllRead() {
        const list = this.getAll();
        list.forEach(item => item.read = true);
        this.save(list);
        this.renderDropdown();
        this.updateBadge();
    },

    delete(id) {
        let list = this.getAll();
        list = list.filter(item => item.id !== id);
        this.save(list);
        this.renderDropdown();
        this.updateBadge();
    },

    clearAll() {
        this.save([]);
        this.renderDropdown();
        this.updateBadge();
    },

    updateBadge() {
        const list = this.getAll();
        const unreadCount = list.filter(item => !item.read).length;
        const badge = document.getElementById('bell-badge');
        if (badge) {
            if (unreadCount > 0) {
                badge.style.display = 'flex';
                badge.textContent = unreadCount;
            } else {
                badge.style.display = 'none';
            }
        }
    },

    showToast(item) {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = 'cs-toast';
        toast.innerHTML = `
            <div class="cs-toast-icon">${item.emoji}</div>
            <div class="cs-toast-body">
                <div class="cs-toast-title">${item.title}</div>
                <div class="cs-toast-desc">${item.message}</div>
            </div>
        `;

        toast.addEventListener('click', () => {
            // Mark as read when clicked
            this.markRead(item.id);
            if (item.actionUrl) {
                window.location.href = item.actionUrl;
            } else {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 400);
            }
        });

        container.appendChild(toast);
        // Force reflow
        toast.offsetHeight;
        toast.classList.add('show');

        // Auto dismiss after 6 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 400);
            }
        }, 6000);
    },

    markRead(id) {
        const list = this.getAll();
        const item = list.find(item => item.id === id);
        if (item) {
            item.read = true;
            this.save(list);
            this.renderDropdown();
            this.updateBadge();
        }
    },

    timeAgo(ts) {
        const diff = Date.now() - ts;
        if (diff < 60000) return 'Just now';
        const mins = Math.floor(diff / 60000);
        if (mins < 60) return `${mins}m ago`;
        const hours = Math.floor(diff / 3600000);
        if (hours < 24) return `${hours}h ago`;
        return new Date(ts).toLocaleDateString();
    },

    renderDropdown() {
        const listContainer = document.querySelector('.nd-list');
        if (!listContainer) return;

        const list = this.getAll();
        if (list.length === 0) {
            listContainer.innerHTML = '<div class="nd-empty">No notifications yet.</div>';
            return;
        }

        listContainer.innerHTML = '';
        list.forEach(item => {
            const row = document.createElement('div');
            row.className = `nd-item ${item.read ? '' : 'unread'}`;
            row.innerHTML = `
                <div class="nd-item-icon">${item.emoji}</div>
                <div class="nd-item-content">
                    <div class="nd-item-msg">${item.message}</div>
                    <div class="nd-item-time">${this.timeAgo(item.timestamp)}</div>
                </div>
                <button type="button" class="nd-item-delete" title="Delete">✕</button>
            `;

            // Row click
            row.addEventListener('click', (e) => {
                if (e.target.classList.contains('nd-item-delete')) {
                    e.stopPropagation();
                    this.delete(item.id);
                    return;
                }
                this.markRead(item.id);
                if (item.actionUrl) {
                    window.location.href = item.actionUrl;
                }
            });

            listContainer.appendChild(row);
        });
    },

    initUI() {
        // Find existing icon-button with 🔔 and refactor it
        const originalButtons = document.querySelectorAll('button.icon-button');
        let bellBtn = null;
        originalButtons.forEach(btn => {
            if (btn.textContent.includes('🔔')) {
                bellBtn = btn;
            }
        });

        if (!bellBtn) return; // No bell button found on this template

        // Add parent wrapper and setup structure
        bellBtn.id = 'bell-btn';
        bellBtn.innerHTML = '🔔<span id="bell-badge" style="display:none;">0</span>';

        const wrapper = document.createElement('div');
        wrapper.className = 'bell-wrapper';
        bellBtn.parentNode.insertBefore(wrapper, bellBtn);
        wrapper.appendChild(bellBtn);

        // Create Dropdown panel
        const dropdown = document.createElement('div');
        dropdown.id = 'notification-dropdown';
        dropdown.innerHTML = `
            <div class="nd-header">
                <h4 class="nd-title">Notifications</h4>
                <button type="button" class="nd-clear-btn" id="nd-clear-all">Clear All</button>
            </div>
            <div class="nd-list"></div>
        `;
        wrapper.appendChild(dropdown);

        // Click handler to toggle dropdown
        bellBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('active');
            if (dropdown.classList.contains('active')) {
                this.markAllRead();
            }
        });

        // Hide dropdown when clicking elsewhere
        document.addEventListener('click', (e) => {
            if (!wrapper.contains(e.target)) {
                dropdown.classList.remove('active');
            }
        });

        // Clear All handler
        document.getElementById('nd-clear-all').addEventListener('click', (e) => {
            e.stopPropagation();
            this.clearAll();
        });

        // Initial render
        this.renderDropdown();
        this.updateBadge();
    }
};

// Scheduler & Triggers Module
const CS_Reminders = {
    // suggestions based on mood
    suggestForMood(mood) {
        if (!mood) return;

        const config = {
            happy: {
                emoji: '😊',
                title: 'High Spirits! 🌟',
                message: 'It is wonderful that you are feeling happy today! Maintain these positive vibes by playing a calming game like Chess or Bubble Pop.',
                url: '/games/'
            },
            excited: {
                emoji: '🤩',
                title: 'Fantastic Energy! ⚡',
                message: 'Love the positive vibe! Channels this great focus into a strategy challenge like Chess or Sudoku!',
                url: '/games/'
            },
            calm: {
                emoji: '😌',
                title: 'Inner Peace 🍃',
                message: 'You are in a centered state of mind. Keep it up by checking your wellness journal or reading a quiet book.',
                url: '/journal/'
            },
            sad: {
                emoji: '😢',
                title: 'Be Gentle 🌸',
                message: 'It is okay to feel low. We suggest trying a comforting Gratitude Meditation or talking to your AI Chatbot companion.',
                url: '/meditation/'
            },
            stress: {
                emoji: '😫',
                title: 'Breathe Out 🌊',
                message: 'Stress can be overwhelming. Take a moment for a deep breathing exercise or listen to relaxing ambient soundscapes.',
                url: '/meditation/'
            },
            angry: {
                emoji: '😡',
                title: 'Mindful Cool Down ❄️',
                message: 'Take a slow, deep breath to release the tension. We recommend a calming breathing session or chatting with the AI Companion.',
                url: '/meditation/'
            }
        };

        const details = config[mood.toLowerCase()];
        if (details) {
            // Delay slightly to let page load settle
            setTimeout(() => {
                CS_Notifications.add(details.emoji, details.title, details.message, details.url);
            }, 800);
        }
    },

    // Water drinking reminder logic
    checkWaterReminder() {
        const lastWater = localStorage.getItem('calmsphere_last_water_time');
        const now = Date.now();

        // Check if manual bypass URL query parameter "?test_water=1" is set
        const urlParams = new URLSearchParams(window.location.search);
        const testWaterTrigger = urlParams.get('test_water') === '1';

        if (!lastWater) {
            localStorage.setItem('calmsphere_last_water_time', now.toString());
            return;
        }

        const elapsed = now - parseInt(lastWater, 10);
        
        // 1 hour = 3600000 ms
        if (elapsed >= 3600000 || testWaterTrigger) {
            // Trigger water reminder
            CS_Notifications.add('💧', 'Hydration Reminder', 'Time to take a break! Drink a fresh glass of water and stretch for a minute.', '/dashboard/');
            localStorage.setItem('calmsphere_last_water_time', now.toString());

            // Clear parameter if test parameter was parsed to prevent endless pop loop
            if (testWaterTrigger) {
                const cleanUrl = window.location.pathname;
                window.history.replaceState({}, document.title, cleanUrl);
            }
        }
    },

    // 30-minute feature suggestions logic
    checkFeatureReminder() {
        const lastFeature = localStorage.getItem('calmsphere_last_feature_time');
        const now = Date.now();

        const urlParams = new URLSearchParams(window.location.search);
        const testFeatureTrigger = urlParams.get('test_feature') === '1';

        if (!lastFeature) {
            localStorage.setItem('calmsphere_last_feature_time', now.toString());
            return;
        }

        const elapsed = now - parseInt(lastFeature, 10);

        // 30 minutes = 1800000 ms
        if (elapsed >= 1800000 || testFeatureTrigger) {
            const features = [
                {
                    emoji: '🧘',
                    title: 'Mindful Meditation',
                    message: 'Take a quiet moment for yourself. Try our guided Sunset Gratitude Meditation to reflect on the good things.',
                    url: '/meditation/'
                },
                {
                    emoji: '🎮',
                    title: 'Zen Games',
                    message: 'Keep your mind sharp! Challenge yourself to a game of Chess or try the Zen Paint-by-Number.',
                    url: '/games/'
                },
                {
                    emoji: '🎧',
                    title: 'Ambient Sounds',
                    message: 'Need to unwind or focus? Play some relaxing ambient sounds like gentle rain or forest waves.',
                    url: '/sound/'
                },
                {
                    emoji: '📚',
                    title: 'Mindful Reading',
                    message: 'Indulge in a moment of wisdom. Check out our collection of self-help and mindfulness books.',
                    url: '/reading/'
                },
                {
                    emoji: '📈',
                    title: 'Monthly Progress Report',
                    message: 'Curious about your progress? Check out your Monthly Report to see your mood patterns and insights.',
                    url: '/monthly-report/'
                },
                {
                    emoji: '✍️',
                    title: 'Expressive Journaling',
                    message: 'Expressing your thoughts helps clear the mind. Write down your feelings in the CalmSphere Journal.',
                    url: '/journal/'
                },
                {
                    emoji: '🤖',
                    title: 'AI Companion Chat',
                    message: 'Need a friendly ear? Have a gentle conversation with your CalmSphere AI companion.',
                    url: '/chatbot/'
                }
            ];

            // Select a random feature suggestion
            const randomIndex = Math.floor(Math.random() * features.length);
            const selected = features[randomIndex];

            CS_Notifications.add(selected.emoji, selected.title, selected.message, selected.url);
            localStorage.setItem('calmsphere_last_feature_time', now.toString());

            // Clear url parameter to prevent loops
            if (testFeatureTrigger) {
                const cleanUrl = window.location.pathname;
                window.history.replaceState({}, document.title, cleanUrl);
            }
        }
    },

    checkTimeOfDayReminders() {
        const now = new Date();
        const hour = now.getHours();
        const todayStr = now.toISOString().split('T')[0];

        const urlParams = new URLSearchParams(window.location.search);
        const testMorning = urlParams.get('test_morning') === '1';
        const testNight = urlParams.get('test_night') === '1';

        // Morning reminder: 5am - 12pm
        if ((hour >= 5 && hour < 12) || testMorning) {
            const lastMorning = localStorage.getItem('calmsphere_last_morning_reminder');
            if (lastMorning !== todayStr || testMorning) {
                CS_Notifications.add('🌅', 'Good Morning! ☀️', 'Start your day with peaceful ambient sounds or by writing your to-do list in the CalmSphere Journal.', '/sound/');
                localStorage.setItem('calmsphere_last_morning_reminder', todayStr);

                if (testMorning) {
                    const cleanUrl = window.location.pathname;
                    window.history.replaceState({}, document.title, cleanUrl);
                }
            }
        }

        // Night reminder: 8pm - 5am
        if ((hour >= 20 || hour < 5) || testNight) {
            const lastNight = localStorage.getItem('calmsphere_last_night_reminder');
            if (lastNight !== todayStr || testNight) {
                CS_Notifications.add('🌙', 'Good Night! ✨', 'Time to wind down. Relax with some calming breathing exercises or chat with your AI Wellness Companion.', '/meditation/breathe/');
                localStorage.setItem('calmsphere_last_night_reminder', todayStr);

                if (testNight) {
                    const cleanUrl = window.location.pathname;
                    window.history.replaceState({}, document.title, cleanUrl);
                }
            }
        }
    },

    initScheduler() {
        // Run checks on page load
        this.checkWaterReminder();
        this.checkFeatureReminder();
        this.checkTimeOfDayReminders();

        // Every 30 seconds check again (for ongoing sessions)
        setInterval(() => {
            this.checkWaterReminder();
            this.checkFeatureReminder();
            this.checkTimeOfDayReminders();
        }, 30000);
    }
};

// Auto initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    CS_Notifications.initUI();
    CS_Reminders.initScheduler();
});
