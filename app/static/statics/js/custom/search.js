document.addEventListener('DOMContentLoaded', function () {
    const searchForm = document.getElementById('searchForm');
    const searchBtn = document.getElementById('searchBtn');
    const resetBtn = document.getElementById('resetBtn');
    const searchQuery = document.getElementById('searchQuery');

    // 검색 버튼 클릭 이벤트
    if (searchBtn) {
        searchBtn.addEventListener('click', function (e) {
            e.preventDefault();
            performSearch();
        });
    }

    // 초기화 버튼 클릭 이벤트
    if (resetBtn) {
        resetBtn.addEventListener('click', function (e) {
            e.preventDefault();
            resetSearch();
        });
    }

    // 엔터 키 검색
    if (searchQuery) {
        searchQuery.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch();
            }
        });
    }

    // 검색 실행 함수
    function performSearch() {
        const query = document.getElementById('searchQuery').value.trim();
        const mode = document.getElementById('searchMode').value;
        const size = document.getElementById('searchSize').value;
        const page = document.getElementById('searchPage').value;
        const dir = document.getElementById('searchDir').value;
        const cursorInput = document.getElementById('searchCursor');

        // URL 파라미터 구성
        const params = new URLSearchParams();

        if (query) {
            params.append('query', query);
        }
        params.append('mode', mode);
        params.append('size', size);
        params.append('page', page);
        params.append('_dir', dir);

        if (cursorInput && cursorInput.value) {
            params.append('cursor', cursorInput.value);
        }

        // 페이지 이동
        const baseUrl = window.location.pathname;
        window.location.href = `${baseUrl}?${params.toString()}`;
    }

    // 검색 초기화 함수
    function resetSearch() {
        const mode = document.getElementById('searchMode').value;
        const size = document.getElementById('searchSize').value;

        // 기본 파라미터만으로 페이지 이동
        const params = new URLSearchParams();
        params.append('mode', mode);
        params.append('size', size);

        const baseUrl = window.location.pathname;
        window.location.href = `${baseUrl}?${params.toString()}`;
    }
});