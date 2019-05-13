export function clearChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

export function openUrlInNewTab(url) {
    const newWindow = window.open(url, '_blank');
    if (newWindow === null) {
        return false;
    }
    newWindow.focus();
    return true;
}
