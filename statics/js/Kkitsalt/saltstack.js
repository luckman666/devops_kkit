
$(document).ready(function() {
        bindSaltKeyAction();
        FontButtonColour();
        bindSaltAllKeyAction();
        bindSyncHostBtn();
        // bindSaltMultiCheck();
        bindSaltDeployAgent()

});
    // 单击行间三个button对key处理js
function bindSaltKeyAction() {
        $("#SaltConfig").on("click","#SaltKeyAction",function () {
            var hostdic={};
            var HostId = $(this).parent().parent().find('input').attr('id');
            var hostname = $(this).parent().parent().find('[name="hostname"]').html();
            var ip_addr = $(this).parent().parent().find('[name="ip_addr"]').html();
            var saltmethod = $(this).attr('name');
            hostdic['id']=HostId;
            hostdic['hostname']=hostname;
            hostdic['ip_addr']=ip_addr;
            hostdic['saltmethod']=saltmethod;

            $(this).attr('disabled','true');
            var jdate=JSON.stringify(hostdic);
            $.post('/salt/keyaction/', {'jdata':jdate,'single':'True'},function(callback) {
                    callbackfuc(callback)
            })
        })
    }

//    变更字体颜色以及相关按钮消失
function FontButtonColour() {
 // var CurrentPath = GetUrlRelativePath();
if (CurrentPath==='/salt/config/'){
    $.each(MinionStatus,function () {
        if ($(this).html() ==='Rejected'){
            $(this).removeClass();
            $(this).addClass('text-warning');
            $(this).parent().find('[name="key.reject"]').removeClass('ellipse-small-yellow');
            $(this).parent().find('[name="key.reject"]').addClass('ellipse-small-gray');
            $(this).parent().find('[name="key.reject"]').attr('disabled','true');
        }
        if ($(this).html() ==='Accepted'){
            $(this).removeClass();
            $(this).addClass('text-success');
            $(this).parent().find('[name="key.accept"]').removeClass('ellipse-small-green');
            $(this).parent().find('[name="key.accept"]').addClass('ellipse-small-gray');
            $(this).parent().find('[name="key.accept"]').attr('disabled','true');
            $(this).parent().find('[name="key.reject"]').removeClass('ellipse-small-yellow');
            $(this).parent().find('[name="key.reject"]').addClass('ellipse-small-gray');
            $(this).parent().find('[name="key.reject"]').attr('disabled','true')
        }
        if ($(this).html() ==='Unaccepted'){
            // console.log($(this).prevAll());
            $(this).parent().find('[name="key.delete"]').removeClass('ellipse-small-red');
            $(this).parent().find('[name="key.delete"]').addClass('ellipse-small-gray');
            $(this).parent().find('[name="key.delete"]').attr('disabled','true')
        }
    })
} else {

}
}


//全部接收key新
function bindSaltAllKeyAction() {
    $('#AllActiontKey').click(function () {
        $.post('/salt/keyaction/', {'saltmethod': 'key.accept','single':'False'},function(callback) {

            var info = JSON.parse(callback);
            if ((info.status)==='error'){
                alert(info.msg)
            }else {
                callbackfuc(callback)
            }
        })
    })
}

//同步配置
function bindSyncHostBtn() {
    $('#sync-host-btn').click(function () {
        var CheckMedat = [];
        $.each(MinionStatus,function () {
            if ($(this).html() ==='Accepted'){
                CheckMedat.push(this)
            }
        });
        if (CheckMedat.length ===0){
            alert('无法同步从属主机信息!系统没有找到从属主机，请先检查从属主机key是否被接受');
            return false
        } else {
      $.post('/salt/syncminion/', {'jdata':'grains.items'},function(callback) {

        var info = JSON.parse(callback);
        })
        }

    })
}

//部署agent
function bindSaltDeployAgent(){
    $("#deployagent").click(function () {
        bindSaltMultiCheck()
    })
}

//多个选择过滤
function bindSaltMultiCheck() {
    var lis = [];
    var AllActive = $("tr[class='CheckAll active']");
    // console.log('AllActive',AllActive);
    $.each(AllActive, function () {
        if ($(this).find('#MinionStatus').html() === 'Unaccepted') {
            var hostdic = {};
            var HostId = $(this).find('input').attr('id');
            var hostname = $(this).find('[name="hostname"]').html();
            var ip_addr = $(this).find('[name="ip_addr"]').html();
            hostdic['id'] = HostId;
            hostdic['hostname'] = hostname;
            hostdic['ip_addr'] = ip_addr;
            lis.push(hostdic);
        }
    });
        $.post('/salt/deployagent/', {'jdata':JSON.stringify(lis)},function(callback) {
            callbackfuc(callback)
    })
}

//执行脚本的js

$('#salt-execute-script-btn').click(function () {
    // console.log('task_expire_time ',task_expire_time );
    postDic = {
        //选择了几个服务器
        'selected_hosts': []
    };
    var err_msg = [];
    //run form submistion check before submit
    var selected_hosts = $("tr[id='TableRow']").filter(".active");

    if (selected_hosts.length == 0) {
        err_msg.push("未选中任何主机执行任务！");
        alert("未选中任何主机执行任务！");
        return false
    }
    // 遍历selected_hosts列表中的内容
    $(selected_hosts).children().children('input').each(function () {

        // {#      添加主机id 类似host_1
        if ($(this).parent().parent().find('[name="hostname"]').html() != ''){
            postDic["selected_hosts"].push($(this).attr("id"));
        } else {

        }

    });
    // {#    序列化    #}
    postDic["selected_hosts"] = JSON.stringify(unique(postDic["selected_hosts"]));
    if (err_msg.length == 0) { // passed form submition check
        // {#    显示模态对话框        #}
        // console.log('postDic',postDic);
        $('#ExecuteScriptModal').modal('show');
        // {#     拿到用户输入的命令，并且去除两边的空格   #}
    } else {
        alert(err_msg);
        return false
    }
});

//上传脚本选择完毕后执行js
function ExecuteScriptConfirm(ele,post_url) {

       var script_expire_time = $('#ExecuteScriptModal').find("#script_expire_time").val();
       var params = {
           'selected_hosts':JSON.parse(postDic['selected_hosts']),
           'expire_time':script_expire_time
       };
        var task_type = $('input:radio[name="optionsRadios"]:checked').val();
        var condition = true;
       // 文件名列表
           var file_list = [];
           $(".file-upload-indicator[title='上传']").parent().parent().children().filter(".file-footer-caption").each(function(){
               file_list.push($(this).html());
           });
           if (file_list.length ===0){
               alert("未选择要上传的脚本！");
               condition = false
           }
           // params['remote_file_path'] = remote_file_path;
           params['local_file_list'] = file_list;
            $("#ExecuteScriptModal").modal('hide');

    if (condition){
        postDic = {'task_type':task_type,'params':JSON.stringify(params)};
          $.post(post_url, postDic,function(callback) {
       // 结果回掉
                callbackfuc(callback)
          })
        }

    }

//查看正在运行中的job

$("#StopSaltJob").click(function () {
$.getJSON('/salt/jobaction/',function(TaskIdList) {
    console.log('TaskIdList.status',TaskIdList);
var DisplayTask = [];

if (TaskIdList.status!=4301){
    $.each(TaskIdList,function (index,task) {
        // if (task != '') {
        console.log('task', task, index);
        var ScriptName = task[0].arg[0].split("/");
        DisplayTask.push("<br> <input type=\"checkbox\" name=\"jid\" id=" + task[0].jid + "  salt_client=" + index + " >   目标主机： " + index + "   任务名称： " + ScriptName[ScriptName.length - 1] + " </br> ")
    // }
    });
    // if (DisplayTask !=[]){
        $("#RunTask").html(DisplayTask);
        $("#RunningJobModal").modal('show');
    // }


}
else {
    alert("当前没有可供停止的任务");
}
})
    });

//job停止任务处理js
function TerminateSaltJob(thi){
    var jslis = [];

   var JidObjLis = $("input[name='jid']:checked");
   console.log('JidObjLis',JidObjLis)
   $.each(JidObjLis,function (index,data) {
       var jsdic = {};
       jsdic['id']=$(this).attr('id');
       jsdic['salt_client']=$(this).attr('salt_client');
       jslis.push(jsdic)
   });

    var jids=JSON.stringify(jslis);
    console.log('jids',jids)
    if (jslis != ''){
        $("#RunningJobModal").modal('hide');
        $.post("/salt/stopiob/", { 'jids':jids},function(callback){
            var backdata =JSON.parse(callback);
            // $.each(backdata,function (index,info) {
                stop_job_show_alert_info(backdata)
            //     console.log('index,info',index,info)
            // })



            // if (callback.indexOf("has terminated") > -1){ //task got terminated..
            //
            //     clearInterval(ResultRefresh);
            //
            //     $("#UnknownTaskModal").modal('hide');
            //
            //     show_alert_info([callback]);
            //
            //      $("#submit_task_confirm").prop("disabled",false);
            // }else{
            //     show_alert_warning([callback]);
            // }
        });//end post
    }else{
        show_alert(['未发现该运行任务，可能已经运行完毕，停止失败！！']);
    }
}

//停止job后的告警模态框
function stop_job_show_alert_info(msg_list){
var err_msg = "";

$.each(msg_list,function (index,data) {
    err_msg += index + ". " + data.msg + "<br/>";
});
var context =( '<h4 class="alert-title">信息反馈</h4>' +
    '<p class="alert-message">' +  err_msg +  '</p>' );

$("#TaskStopModal").modal('show');
$("#TaskStopContextDisplay").html(context);

}




