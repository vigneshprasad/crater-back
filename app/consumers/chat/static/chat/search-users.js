$( document ).ready(function() {
    $('#search-users').on('input', function(event) {
        let value = event.target.value;
        $('.user-detail').show();
        if (value) {
            $('.user-detail').filter(function() {
                return !($(this).find('.username').text().toLowerCase().indexOf(value.toLowerCase()) > -1)
            }).hide();
        }
    });
    let objDiv = document.getElementById('messages__block');
    if (objDiv) {
        objDiv.scrollTop = objDiv.scrollHeight;
    }
});
