$(document).ready(function() {
// CheckLog()
});

// 查看日志点击确认查看后执行js
function CheckLog(){

    var selected_hosts = $("input:radio[name=\"host\"]").eq(0).attr("checked",'checked').attr('id');

if (selected_hosts == '') {

    alert("未选中任何主机执行任务！");
    return false
} else {
            console.log('selected_hosts',selected_hosts);
            selected_hosts=JSON.stringify(selected_hosts);
              $.post("/api/check_host_software_log/", {'selected_hosts':selected_hosts},function(callback) {
                console.log(callback)
            })
}



}