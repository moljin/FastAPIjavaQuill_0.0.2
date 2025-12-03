export const minimalToolbar = [
    'bold', 'strike',
    'link', //{'header': 3},
    {'list': 'ordered'}, {'list': 'bullet'}, 'code-block',
    {'script': 'sub'}, {'script': 'super'}, 'image', 'video'
];

export class MinimalCustomizer {
    constructor(quill, options) {
        this.quill = quill;
        this.options = options;

        // 내부 상태
        this.toolbarEl = null;
        this.isMounted = false;

        this._mountWhenToolbarReady();
        this._updateToolbar();

        // 다른 커스터마이징이 있다면 유지
        if (typeof this.restoreEditorContent === 'function') {
            this.restoreEditorContent();
        }
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
            this.isMounted = true;
        };
        tryMount();
    }

    _updateToolbar() {
        //버튼 간 gap: 5px
        const qlFormats = this.toolbarEl.querySelector(':scope > span.ql-formats');
        qlFormats.style.gap = "5px";
        // 취소선 버튼 아이콘 크기 조정
        const strikeButton = this.toolbarEl.querySelector(':scope button.ql-strike');
        if (strikeButton) {strikeButton.style.marginBottom = '2px';}
        const strikeSVG = this.toolbarEl.querySelector(':scope button.ql-strike > svg');
        if (strikeSVG) {
            strikeSVG.setAttribute('viewBox', '0 0 17 17');
            const fills = strikeSVG.querySelectorAll(':scope path.ql-fill');
            fills.forEach(fill => {
                fill.style.stroke = 'white';
                fill.style.strokeWidth = '0.7';
            });
        }
        // H3 굵기 조정
        const h3 = this.toolbarEl.querySelector(':scope button.ql-header > svg > path');
        if (h3) {
            h3.style.stroke = 'white';
            h3.style.strokeWidth = '0.7';
        }
        // 위, 아랫 첨자 굵기 조정
        const scripts = this.toolbarEl.querySelectorAll(':scope button.ql-script');
        scripts.forEach(script => {
            script.querySelectorAll('svg').forEach(svg => {
                const secondPath = svg.querySelector('path:nth-of-type(2)');
                if (secondPath) {
                    secondPath.style.stroke = 'white';
                    secondPath.style.strokeWidth = '0.7';
                }
            });
        });



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

}