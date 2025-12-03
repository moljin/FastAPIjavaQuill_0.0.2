// document.addEventListener('DOMContentLoaded', function () {
//     // 이미지가 들어있는 p요소의 상황에 따라 이미지 margin 수정
//     const paragraphs = document.querySelectorAll('.object-content p');
//
//     paragraphs.forEach(p => {
//         console.log(p);
//         console.log(p.innerHTML, p.textContent);
//         const textContent = p.textContent.trim();
//         const pImg = p.querySelector('img');
//
//         if (pImg) {
//             if (textContent.length > 0) {
//                 pImg.style.marginTop = '20px';
//             } else {
//                 // 텍스트가 없고 이미지만 있는 경우: 기본 동작 유지
//             }
//         } else {
//             // 이미지가 없는 경우: 기본 동작 유지
//         }
//     });
//
//     // 실제 실행: 'object-content' div 내의 불필요한 빈 태그를 제거합니다.
//     removeEmptyTrailingTags('object-content');
// });

// // 빈 태그(텍스트/미디어가 전혀 없는 요소)가 뒤에 연속될 경우 제거
// function removeEmptyTrailingTags(containerId) {
//     const container = document.getElementById(containerId);
//     if (!container) {
//         console.error(`Container with id "${containerId}" not found.`);
//         return;
//     }
//
//     const children = Array.from(container.children);
//     let lastContentfulIndex = -1;
//
//     // 내용(텍스트, 이미지, 비디오 등)이 있는 마지막 자식 요소의 인덱스를 찾습니다.
//     for (let i = children.length - 1; i >= 0; i--) {
//         const child = children[i];
//
//         const hasContent =
//             (child.textContent.trim() !== '') ||
//             (child.querySelector('img, video, audio, iframe') !== null) ||
//             (child.tagName.toLowerCase() === 'img') ||
//             (child.tagName.toLowerCase() === 'video') ||
//             (child.tagName.toLowerCase() === 'audio') ||
//             (child.tagName.toLowerCase() === 'iframe');
//
//         if (hasContent) {
//             lastContentfulIndex = i;
//             break;
//         }
//     }
//
//     // 마지막 내용 요소 이후의 모든 태그를 삭제합니다.
//     if (lastContentfulIndex !== -1 && lastContentfulIndex < children.length - 1) {
//         for (let i = children.length - 1; i > lastContentfulIndex; i--) {
//             container.removeChild(children[i]);
//         }
//     }
// }


document.addEventListener('DOMContentLoaded', function () {
    // 이미지가 들어있는 p요소의 상황에 따라 이미지 margin 수정
    const paragraphs = document.querySelectorAll('.object-content p');
    paragraphs.forEach(p => {
        const textContent = p.textContent.trim();
        const pImg = p.querySelector('img');
        if (pImg) {
            if (textContent.length > 0) {
                pImg.style.marginTop = '20px';
            }
        }
    });

    // 기존 로직 유지: 'object-content' id 내의 불필요한 빈 태그 제거
    // removeEmptyTrailingTags('object-content'); 아래로 통합했다.
    removeEmptyParagraphsInContainer('#object-content'); // .object-content.article.content

    // 추가: upper/lower 컨테이너 내부의 빈 p(<p><br></p> 등) 제거
    removeEmptyParagraphsInContainer('.object-content.comment.content');
    removeEmptyParagraphsInContainer('.object-content.reply.content');
});

// 빈 태그(텍스트/미디어가 전혀 없는 요소)가 뒤에 연속될 경우 제거 (기존 함수)
function removeEmptyTrailingTags(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const children = Array.from(container.children);
    let lastContentfulIndex = -1;

    for (let i = children.length - 1; i >= 0; i--) {
        const child = children[i];
        const hasContent =
            (child.textContent.trim() !== '') ||
            (child.querySelector && child.querySelector('img, video, audio, iframe') !== null) ||
            (child.tagName && child.tagName.toLowerCase() === 'img');

        if (hasContent) {
            lastContentfulIndex = i;
            break;
        }
    }

    if (lastContentfulIndex >= 0 && lastContentfulIndex < children.length - 1) {
        for (let i = children.length - 1; i > lastContentfulIndex; i--) {
            children[i].remove();
        }
    }
}

// // 추가: 특정 컨테이너 내부의 "실제 텍스트나 미디어가 없는" 빈 p 태그 제거
// function removeEmptyParagraphsInContainer(containerSelector) {
//     const containers = document.querySelectorAll(containerSelector);
//     if (!containers) return;
//     containers.forEach(function (container) {
//         const ps = container.querySelectorAll('p');
//         console.log(ps);
//         ps.forEach(p => {
//             // 미디어가 포함되어 있으면 유지
//             const hasMedia = p.querySelector('img, video, audio, iframe') !== null;
//             if (hasMedia) return;
//
//             // 텍스트(공백, 제로폭 문자 제거)가 비어있는지 확인
//             const normalizedText = (p.textContent || '').replace(/\u200B/g, '').trim();
//
//             // 자식 노드가 br 또는 공백 텍스트만으로 이루어졌는지 확인
//             const onlyBrsAndWhitespace = Array.from(p.childNodes).every(node => {
//                 if (node.nodeType === Node.ELEMENT_NODE) {
//                     const tag = node.tagName.toLowerCase();
//                     // 에디터가 만드는 비어 있는 span 등을 대비해 텍스트도 함께 확인
//                     if (tag === 'br') return true;
//                     if ((tag === 'span' || tag === 'em' || tag === 'strong' || tag === 'b' || tag === 'i') &&
//                         node.textContent.replace(/\u200B/g, '').trim() === '') return true;
//                     return false;
//                 } else if (node.nodeType === Node.TEXT_NODE) {
//                     return node.textContent.replace(/\u200B/g, '').trim() === '';
//                 } else {
//                     // 주석 등은 콘텐츠로 보지 않음
//                     return true;
//                 }
//             });
//
//             if (normalizedText === '' && onlyBrsAndWhitespace) {
//                 p.remove();
//             }
//         });
//     });
//
//
// }

// 추가: 특정 컨테이너 내부의 "실제 텍스트나 미디어가 없는" 빈 p 태그 제거 (끝부분만)
function removeEmptyParagraphsInContainer(containerSelector) {
    const containers = document.querySelectorAll(containerSelector);
    if (!containers) return;

    containers.forEach(function (container) {
        const ps = container.querySelectorAll('p');
        console.log(ps);

        // 마지막 컨텐츠가 있는 p 태그의 인덱스를 찾기
        let lastContentfulIndex = -1;

        for (let i = ps.length - 1; i >= 0; i--) {
            const p = ps[i];

            // 미디어가 포함되어 있으면 컨텐츠가 있다고 판단
            const hasMedia = p.querySelector('img, video, audio, iframe') !== null;
            if (hasMedia) {
                lastContentfulIndex = i;
                break;
            }

            // 텍스트(공백, 제로폭 문자 제거)가 있는지 확인
            const normalizedText = (p.textContent || '').replace(/\u200B/g, '').trim();

            if (normalizedText !== '') {
                lastContentfulIndex = i;
                break;
            }

            // 자식 노드 중에 실제 컨텐츠가 있는지 확인
            const hasRealContent = Array.from(p.childNodes).some(node => {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    const tag = node.tagName.toLowerCase();
                    // br 태그나 빈 인라인 요소는 실제 컨텐츠로 보지 않음
                    if (tag === 'br') return false;
                    if ((tag === 'span' || tag === 'em' || tag === 'strong' || tag === 'b' || tag === 'i') &&
                        node.textContent.replace(/\u200B/g, '').trim() === '') return false;
                    return true; // 다른 요소들은 컨텐츠로 간주
                } else if (node.nodeType === Node.TEXT_NODE) {
                    return node.textContent.replace(/\u200B/g, '').trim() !== '';
                }
                return false;
            });

            if (hasRealContent) {
                lastContentfulIndex = i;
                break;
            }
        }

        // 마지막 컨텐츠 이후의 빈 p 태그들만 제거
        if (lastContentfulIndex >= 0 && lastContentfulIndex < ps.length - 1) {
            for (let i = ps.length - 1; i > lastContentfulIndex; i--) {
                ps[i].remove();
            }
        }
    });
}