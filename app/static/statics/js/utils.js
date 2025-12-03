export function UTCtoKST(utcDateString) {
// "Z"를 추가하여 입력 문자열이 UTC 기준임을 명시합니다.
    const dateObject = new Date(utcDateString + "Z");

    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false, // 24시간 형식
        timeZone: 'Asia/Seoul' // 한국 시간대 지정
    };

    // 'en-CA' (캐나다 영어) 로케일은 YYYY-MM-DD 형식을 기본으로 하여 시작이 편리합니다.
    // 그리고 공백으로 시, 분, 초를 구분하도록 문자열을 가공합니다.
    // " at " 문자열을 공백으로 변경
    return new Intl.DateTimeFormat('en-CA', options)
        .format(dateObject)
        .replace(/,/, "") // 쉼표 제거 (en-CA 형식의 기본 출력에 포함될 수 있음)
        .replace(" at ", " ");

}