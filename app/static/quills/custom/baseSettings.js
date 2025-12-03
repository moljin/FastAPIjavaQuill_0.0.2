export const baseToolbar = [
    ['bold', 'italic', 'underline', 'strike'],
    ['link', 'image', 'video'],
    [{'header': 1}, {'header': 2}, {'header': 3}],
    [{'list': 'ordered'}, {'list': 'bullet'}, {'list': 'check'}, {'indent': '-1'}, {'indent': '+1'}],
    ['blockquote', 'code-block'],
    [{'script': 'sub'}, {'script': 'super'}, 'formula'],
    [{'color': []}, {'background': []}, {'align': ['', 'center', 'right', 'justify']}],
];

export class QuillCustomizer {
    constructor(quill, options) {
        this.quill = quill;
        this.options = options || {};

        // 내부 상태
        this.toolbarEl = null;
        this.dropdownWrapper = null;
        this.dropdownToggle = null;
        this.dropdownMenu = null;
        this.groupEls = new Map();       // groupClass -> HTMLElement
        this.placeholders = new Map();   // groupClass -> Comment
        this.resizeHandler = null;
        this.isMounted = false;

        // 반응형에 사용할 브레이크포인트 정의
        this.breakpoints = [
            { width: 1470, group: 'group-extra' },
            { width: 1355,  group: 'group-script' },
            { width: 1170,  group: 'group-block' },
            { width: 750,  group: 'group-list-indent' },
            { width: 545,  group: 'group-header' },
        ];

        // 초기 디자인(그룹 클래스 지정 등)
        this.toolbarDesign();
        // 툴바가 준비된 뒤에 반응형 셋업
        this._mountWhenToolbarReady();

        // 다른 커스터마이징이 있다면 유지
        if (typeof this.restoreEditorContent === 'function') {
            this.restoreEditorContent();
        }
    }

    // 기존 nth-child → 의미 있는 클래스명으로 지정
    toolbarDesign() {
        // toolbar는 Quill 모듈에서 가져오는 것이 가장 안전
        const toolbarModule = this.quill.getModule('toolbar');
        const toolbarElement = toolbarModule ? toolbarModule.container : document.querySelector("#editor-container > div.ql-toolbar.ql-snow");
        if (!toolbarElement) return;

        // 순서: baseToolbar 기준
        const groups = toolbarElement.querySelectorAll(':scope > span.ql-formats');
        if (!groups || groups.length === 0) return;

        // 1: 텍스트, 2: 삽입, 3: 헤더, 4: 목록/인덴트, 5: 블록, 6: 스크립트, 7: 추가(색/정렬)
        const mapping = [
            'group-text',
            'group-insert',
            'group-header',
            'group-list-indent',
            'group-block',
            'group-script',
            'group-extra',
        ];

        groups.forEach((el, i) => {
            const cls = mapping[i];
            if (cls) {
                el.classList.add(cls);
            }
        });
    }

    _mountWhenToolbarReady() {
        const tryMount = () => {
            const toolbarModule = this.quill.getModule('toolbar');
            const toolbar = toolbarModule ? toolbarModule.container : document.querySelector("#editor-container > div.ql-toolbar.ql-snow");
            if (!toolbar) {
                // 툴바가 아직 준비되지 않았다면 다음 틱에 재시도
                setTimeout(tryMount, 0);
                return;
            }
            this.toolbarEl = toolbar;
            this._initResponsiveToolbar();
            this.isMounted = true;
        };
        tryMount();
    }

    _initResponsiveToolbar() {
        if (!this.toolbarEl) return;

        // 드롭다운 래퍼 만들기 (툴바 내부에 넣어야 이벤트 핸들러가 살아있음)
        this.dropdownWrapper = document.createElement('div');
        this.dropdownWrapper.className = 'ql-formats dropdown-wrapper';
        this.dropdownWrapper.style.display = 'none';

        this.dropdownToggle = document.createElement('div');
        this.dropdownToggle.className = 'dropdown-toggle';
        this.dropdownToggle.setAttribute('aria-expanded', 'false');
        this.dropdownToggle.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3.94 15.75"><g><path d="M12.28,7.69a1.92,1.92,0,0,1-1.39-.58,2,2,0,0,1-.58-1.39,1.92,1.92,0,0,1,.58-1.39,2,2,0,0,1,1.39-.58,1.92,1.92,0,0,1,1.39.58,2,2,0,0,1,.58,1.39,1.92,1.92,0,0,1-.58,1.39,2,2,0,0,1-1.39.58Zm0,2a1.92,1.92,0,0,1,1.39.58,2,2,0,0,1,.58,1.39A1.92,1.92,0,0,1,13.67,13a2,2,0,0,1-1.39.58A1.92,1.92,0,0,1,10.89,13a2,2,0,0,1-.58-1.39,2,2,0,0,1,2-2Zm0,5.9a1.92,1.92,0,0,1,1.39.58,2,2,0,0,1,.58,1.39,1.92,1.92,0,0,1-.58,1.39,2,2,0,0,1-1.39.58,1.92,1.92,0,0,1-1.39-.58,2,2,0,0,1-.58-1.39,1.92,1.92,0,0,1,.58-1.39,1.94,1.94,0,0,1,1.39-.58Z" transform="translate(-10.31 -3.75)"></path></g></svg>`;

        this.dropdownMenu = document.createElement('div');
        this.dropdownMenu.className = 'dropdown-menu';
        this.dropdownMenu.style.display = 'none'; // 토글 시에 표시

        this.dropdownWrapper.appendChild(this.dropdownToggle);
        this.dropdownWrapper.appendChild(this.dropdownMenu);
        this.toolbarEl.appendChild(this.dropdownWrapper);

        // 드롭다운 토글
        this.dropdownToggle.addEventListener('click', () => {
            const opened = this.dropdownMenu.style.display === 'inline-flex';
            if (opened) {
                this.dropdownMenu.style.display = 'none';
                this.dropdownToggle.setAttribute('aria-expanded', 'false');
            } else {
                this.dropdownMenu.style.display = 'inline-flex';
                this.dropdownToggle.setAttribute('aria-expanded', 'true');
            }
        });

        // 관리할 그룹 요소 수집 및 placeholder 삽입(원위치 복귀용)
        const allGroups = new Set(this.breakpoints.map(b => b.group));
        // strike 아이콘 조정용: group-text도 찾음
        allGroups.add('group-text');

        for (const groupCls of allGroups) {
            const el = this.toolbarEl.querySelector(`:scope > .${groupCls}`);
            if (el) {
                this.groupEls.set(groupCls, el);
                const ph = document.createComment(`placeholder:${groupCls}`);
                el.parentNode.insertBefore(ph, el);
                this.placeholders.set(groupCls, ph);
            }
        }

        // 디바운스된 리사이즈 핸들러
        this.resizeHandler = this._debounce(() => this._updateToolbar(), 16);
        window.addEventListener('resize', this.resizeHandler, { passive: true });

        // 최초 적용
        this._updateToolbar();
    }

    _updateToolbar() {
        if (!this.toolbarEl) return;

        const winWidth = window.innerWidth;

        // 취소선 버튼 아이콘 크기 조정
        const strikeSVG = this.toolbarEl.querySelector(':scope > span.ql-formats.group-text > button.ql-strike > svg');
        if (strikeSVG) {
            strikeSVG.setAttribute('viewBox', '0 0 16 16');
        }

        // 드롭다운 초기화
        this.dropdownMenu.style.display = 'none';
        this.dropdownMenu.innerHTML = '';
        this.dropdownWrapper.style.display = 'none';
        this.dropdownToggle.setAttribute('aria-expanded', 'false');

        // 각 그룹을 조건에 따라 이동(복제 X, 원본 이동)
        let movedCount = 0;

        for (const bp of this.breakpoints) {
            const groupEl = this.groupEls.get(bp.group);
            if (!groupEl) continue;

            if (winWidth < bp.width) {
                // 드롭다운으로 이동
                if (groupEl.parentNode !== this.dropdownMenu) {
                    this.dropdownMenu.appendChild(groupEl);
                }
                groupEl.style.display = 'flex';
                movedCount++;
            } else {
                // 원위치로 복귀
                const ph = this.placeholders.get(bp.group);
                if (ph && groupEl.parentNode !== ph.parentNode) {
                    ph.parentNode.insertBefore(groupEl, ph.nextSibling);
                }
                groupEl.style.display = 'inline-flex';
            }
        }

        // 드롭다운 보이기/숨기기
        if (movedCount > 0) {
            this.dropdownWrapper.style.display = 'inline-flex';
            this.dropdownToggle.style.display = 'block';
        } else {
            this.dropdownWrapper.style.display = 'none';
        }
    }

    // 유틸: 간단한 디바운스
    _debounce(fn, wait) {
        let t = null;
        return (...args) => {
            if (t) clearTimeout(t);
            t = setTimeout(() => fn.apply(this, args), wait);
        };
    }

    restoreEditorContent() {
            if (this.options.objectId && this.options.initialContent) {
                try {
                    this.quill.root.innerHTML = this.options.initialContent;
                } catch (e) {
                    console.warn("콘텐츠 복원 중 오류 발생:", e);
                }
            }
        }

    // 필요 시 모듈 해제
    destroy() {
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
            this.resizeHandler = null;
        }
        if (this.dropdownWrapper && this.dropdownWrapper.parentNode) {
            this.dropdownWrapper.parentNode.removeChild(this.dropdownWrapper);
        }
        this.groupEls.clear();
        this.placeholders.clear();
        this.isMounted = false;
    }
}