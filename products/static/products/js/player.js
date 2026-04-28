document.addEventListener('DOMContentLoaded', () => {
    const musicContainer = document.getElementById('welcome-music-container');
    if (!musicContainer) return;

    const audio = document.getElementById('welcome-audio');
    const controlBtn = document.getElementById('audio-control-btn');
    const mainIcon = document.getElementById('main-icon');
    
    const countdownContainer = document.getElementById('countdown-container');
    const countdownText = document.getElementById('countdown-text');
    
    const trackInfoContainer = document.getElementById('track-info-container');
    const trackTitle = document.getElementById('track-title');
    const trackArtist = document.getElementById('track-artist');
    
    const currentTimeEl = document.getElementById('current-time');
    const totalDurationEl = document.getElementById('total-duration');
    const progressFilled = document.getElementById('progress-filled');

    let isCancelledByUser = false;
    let isAutoplayBlocked = false;

    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    function setTrackMetadata() {
        const audioSrc = audio.src;
        const fileName = audioSrc.split('/').pop().replace(/\.[^/.]+$/, "");
        const formattedName = fileName.replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        
        trackTitle.textContent = formattedName;
        trackArtist.textContent = "Welcome Music";
    }

    function updateProgress() {
        if (!audio.duration) return;
        const progressPercent = (audio.currentTime / audio.duration) * 100;
        progressFilled.style.width = `${progressPercent}%`;
        currentTimeEl.textContent = formatTime(audio.currentTime);
    }
    
    audio.addEventListener('loadedmetadata', () => {
        totalDurationEl.textContent = formatTime(audio.duration);
    });
    audio.addEventListener('timeupdate', updateProgress);

    let countdown = 3;
    setTrackMetadata(); 
    countdownText.textContent = `پخش خودکار تا  ${countdown} ثانیه دیگر`;
    
    const countdownTimer = setInterval(() => {
        if (isCancelledByUser) {
            clearInterval(countdownTimer);
            return;
        }
        countdown--;
        if (countdown > 0) {
            countdownText.textContent = `پخش خودکار تا  ${countdown} ثانیه دیگر`;
        } else {
            clearInterval(countdownTimer);
            attemptInitialPlay();
        }
    }, 1000);

    function attemptInitialPlay() {
        if (isCancelledByUser) return;
        setPlayingState();
        const playPromise = audio.play();
        if (playPromise !== undefined) {
            playPromise.catch(() => {
                isAutoplayBlocked = true;
                document.addEventListener('click', unlockAudio, { once: true });
                document.addEventListener('touchstart', unlockAudio, { once: true });
            });
        }
    }

    function unlockAudio() {
        if (isAutoplayBlocked && audio.paused) {
            audio.play().then(() => {
                isAutoplayBlocked = false;
                setPlayingState();
            });
        }
    }

    controlBtn.addEventListener('click', () => {
        isCancelledByUser = true;
        isAutoplayBlocked = false;
        clearInterval(countdownTimer);
        document.removeEventListener('click', unlockAudio);
        document.removeEventListener('touchstart', unlockAudio);
        
        if (audio.paused) {
            audio.play();
        } else {
            audio.pause();
        }
    });
    
    audio.onplaying = () => setPlayingState();
    audio.onpause = () => setPausedState();
    
    function setPlayingState() {
        musicContainer.classList.remove('paused');
        mainIcon.className = 'fas fa-pause';
        countdownContainer.style.display = 'none';
        trackInfoContainer.style.display = 'block';
    }

    function setPausedState() {
        musicContainer.classList.add('paused');
        mainIcon.className = 'fas fa-play';
    }
});
