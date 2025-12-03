import {ImageResize, imageInsertByToolbarButton, videoInsertByToolbarButton} from "./mediaHandler.js";

export default function quillClient(editorElement, toolbar, quillCustomizer, _objectID=null, _editorContent=null) {
    const Quill = window.Quill;
    editorElement.style.minHeight = '300px';

    if (!Quill.imports || !Quill.imports['modules/quillCustomizer']) {
        Quill.register('modules/quillCustomizer', quillCustomizer);
    }
    if (!Quill.imports || !Quill.imports['modules/imageResize']) {
        Quill.register('modules/imageResize', ImageResize, true);
    }

    const quillModulesConfig = {
        syntax: true,              // Highlight syntax module
        toolbar: {
            container: toolbar,
            handlers: {
                image: imageInsertByToolbarButton,
                video: videoInsertByToolbarButton,
            }
        },
        imageResize: {
            modules: ['Resize', 'DisplaySize', 'Toolbar'],
            displayStyles: {backgroundColor: 'black', border: 'none', color: 'white'},
            handleStyles: {backgroundColor: '#fff', border: '1px solid #777', width: '10px', height: '10px'}
        },
        quillCustomizer: {
        objectId: typeof _objectID !== "undefined" ? _objectID : null,
        initialContent: typeof _editorContent !== "undefined" ? _editorContent : null
        },


    };

    return new Quill(editorElement, {
        theme: 'snow',
        placeholder: '여기에 내용을 입력하세요...',
        modules: quillModulesConfig
    });
}





