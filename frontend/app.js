document.addEventListener('DOMContentLoaded', () => {
    const ratingInput = document.getElementById('min-rating');
    const ratingVal = document.getElementById('rating-val');
    const analyzeBtn = document.getElementById('analyze-btn');
    const userInput = document.getElementById('user-input');
    
    const loadingState = document.getElementById('loading');
    const resultsSection = document.getElementById('results');
    
    const badgeSentiment = document.getElementById('badge-sentiment');
    const psychText = document.getElementById('psych-text');
    const movieGrid = document.getElementById('movie-grid');

    // Update rating value display
    ratingInput.addEventListener('input', (e) => {
        ratingVal.textContent = parseFloat(e.target.value).toFixed(1);
    });

    analyzeBtn.addEventListener('click', async () => {
        const text = userInput.value.trim();
        if (!text) {
            alert('Vui lòng chia sẻ tâm trạng của bạn trước nhé!');
            return;
        }

        const rating = parseFloat(ratingInput.value);

        // Hide results, show loading
        resultsSection.classList.add('hidden');
        loadingState.classList.remove('hidden');
        analyzeBtn.disabled = true;

        try {
            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    min_rating: rating
                })
            });

            if (!response.ok) {
                throw new Error('Lỗi từ Server');
            }

            const data = await response.json();
            
            // Populate Results
            renderResults(data);

            // Show results, hide loading
            loadingState.classList.add('hidden');
            resultsSection.classList.remove('hidden');
            
            // Scroll to results smoothly
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            alert('Đã có lỗi xảy ra. Hãy chắc chắn Server đang chạy!');
            console.error(error);
            loadingState.classList.add('hidden');
        } finally {
            analyzeBtn.disabled = false;
        }
    });

    function renderResults(data) {
        // 1. Phân tích tâm lý
        // Typying effect cho lời khuyên
        psychText.textContent = "";
        const textToType = data.psychological_analysis;
        let i = 0;
        
        // Cập nhật Badge (Dựa vào nội dung nếu server trả về, hoặc dựa vào keywords/genres)
        // Hiện tại Server không trả về user_mood trực tiếp, nhưng ta có thể trick bằng cách
        // nếu rating bị đẩy lên 7.5 tự động hoặc từ khóa có chữ buồn thì báo Negative
        // Cách tốt nhất là mượn API trả thêm user_mood. Tạm thời hiển thị:
        badgeSentiment.textContent = "Đã phân tích xong ✓";
        badgeSentiment.className = "badge";

        function typeWriter() {
            if (i < textToType.length) {
                psychText.textContent += textToType.charAt(i);
                i++;
                setTimeout(typeWriter, 10);
            }
        }
        typeWriter();

        // 2. Danh sách phim
        movieGrid.innerHTML = '';
        if (data.movies && data.movies.length > 0) {
            data.movies.forEach((movie, index) => {
                const card = document.createElement('div');
                card.className = 'glass-panel movie-card fade-in';
                card.style.animationDelay = `${index * 0.1}s`;

                // Xử lý chuỗi genres (bỏ dấu ngoặc vuông nếu có)
                let genresStr = movie.genres.replace(/[\[\]']/g, '');

                card.innerHTML = `
                    <div class="movie-header">
                        <div>
                            <div class="movie-title">${movie.title} <span class="movie-year">(${movie.year})</span></div>
                        </div>
                        <div class="movie-rating"><i class="fa-solid fa-star"></i> ${movie.rating}</div>
                    </div>
                    <div class="movie-genres">${genresStr}</div>
                    <div class="movie-director"><i class="fa-solid fa-clapperboard"></i> ${movie.director}</div>
                    <div class="movie-plot">${movie.document.split('Plot: ')[1] || movie.document}</div>
                `;
                movieGrid.appendChild(card);
            });
        } else {
            movieGrid.innerHTML = '<p style="text-align:center; grid-column: 1/-1;">Rất tiếc, không tìm thấy phim phù hợp.</p>';
        }
    }
});
