<template>
    <div>
        <h2>Car Simulation</h2>
        <div id="car-status-area">
            <!-- <el-input type="textarea" :rows="10" placeholder="请输入内容" v-model="textarea">
            </el-input> -->
            <!-- <div id="car-img">
                <el-image :src="'data:image/png;base64,'+pic" :fit="fit">
                    <div slot="error" class="image-slot">
                        <i class="el-icon-picture-outline"></i>
                    </div>
                </el-image>
            </div> -->
            
            <!-- <div class="log">
                <div class="log_text" id='log_list'>
                    <div id="log_text"></div>
                </div>
            </div> -->

            <!-- <div id="log">
                <h4>Log Now:</h4>
                <p>{{ car_log }}</p>
            </div>

            <div id="car">
                <h4>Log Now:</h4>
                <p>{{ car_status }}</p>
            </div> -->

            <div id="car-operation">
                <el-row>
                    <!-- <el-button type="primary" @click="start" round>START</el-button> -->
                    <el-button type="primary" @click="log" round>DAA</el-button>
                    <!-- <el-button type="primary" @click="show_log" round>Show LOG</el-button> -->

                </el-row>                
            </div>

            <div id="time">
                <h4>Time Now:</h4>
                <p>{{date | dateFormat()}}</p>
            </div>
            
            <div id="jump">
                <el-button type="primary" @click="skg" round>SKG Details</el-button>
            </div>

            <div id="jump">
                <el-button type="primary" @click="jumptest" round>Blue page</el-button>
            </div>
            
            <!-- <div id="jump3">
                <el-button type="primary" @click="jump3" round>jump3</el-button>
            </div> -->
            
            <!-- <div id="jump2">
                <a href="../../static/skg.html">Jump</a>
            </div> -->

            <div id="log">
                <!-- 添加按钮 -->
                <!-- <el-button type="primary" style="float: right;" @click="addRow(tableData.length)">添加</el-button> -->
                <!-- 表格 -->
                <el-table 
                    :data="tableData" 
                    style="width: 100%; background-color:lightskyblue;"   
                    ref="tb" 
                    :row-class-name="tableRowClassName" 
                    @current-change="handleRadioChange"
                    :header-cell-style="{background:'transparent', color:'#ffd220'}"
                    :cell-style="{background:'transparent'}"
                >
                    <el-table-column 
                        fixed 
                        prop="log" 
                        label="LOG" 
                        style="width: 100%; "    
                    >
                    
                    </el-table-column>
                    <!-- <el-table-column prop="name" label="姓名" ></el-table-column>
                    <el-table-column prop="province" label="本地" > -->
                    <!-- 单选框部分 -->
                        <!-- <template slot-scope="scope">
                            <el-radio  v-model="radio" :label="scope.row.index">本地</el-radio>
                        </template>
                    </el-table-column> -->
                    <!-- <el-table-column fixed="right" label="操作" >
                        <template slot-scope="scope">
                                <el-button @click.native.prevent="deleteRow(scope.$index, tableData)" type="text" size="small">移除</el-button>
                        </template>
                    </el-table-column> -->
                </el-table>

            </div>
        </div>

        
    </div>
   
       
</template>


<script>
    export default {
        name: 'car_simulation',
        data() {

            return {
                textarea: '',
                pic: "",
                pageTitle: 'Car simulation',
                car_status:"waiting connection...",
                car_log:" ",
                new_log:false,
                log_spice:new Array(),
                date:new Date(),
                // 给一个默认行
			    tableData: [{
					log: 'info: Hello!'
				}],
            }
                
        },

        filters:{
            dateFormat(){
                // var val=JSON.parse(time);
                var date = new Date();
                var year=date.getFullYear();
                var month=date.getMonth();
                var month= date.getMonth()+1<10 ? "0"+(date.getMonth()+1) : date.getMonth()+1;
                var day=date.getDate()<10 ? "0"+date.getDate() : date.getDate();
                var hours=date.getHours()<10 ? "0"+date.getHours() : date.getHours();
                var minutes=date.getMinutes()<10 ? "0"+date.getMinutes() : date.getMinutes();
                var seconds=date.getSeconds()<10 ? "0"+date.getSeconds() : date.getSeconds();
                // 拼接
                return year+"-"+month+"-"+day+" "+hours+":"+minutes+":"+seconds;
            }
        },

        methods: {

            // getlog(){
            //     let xhr = new XMLHttpRequest(),
            //     okStatus = document.location.protocol === "file:" ? 0:200;
            //     xhr.open('GET','/home/quantum-test/code/flask-vue/backend/app/hehe.txt', false);
            //     xhr.overrideMimeType("text/html;charset=utf-8");
            //     xhr.send(null);
            //     console.log(xhr.responseText);
            // },

            start() {
                var param = {
                    "car": this.textarea
                }
                this.axios.post("/car/A/start", param).then(
                    res => {
                        this.car_status = res.data
                        console.info('hello hello hello')

                        console.log(res.data)
                    }
                ).catch(res => {
                    console.log(res.data.res)
                })

               
            },

            log(){
                var param = {
                    "car": this.textarea
                }
                this.axios.post("/car/A/generation_log", param).then(
                    res => {
                        console.info('generation log')
                        // this.car_log = _log.data
                    }
                ).catch(res => {
                    // console.log(_log.data.res)
                })
            },

            show_log(){
                var param = {
                    "car": this.textarea
                }
                this.axios.post("/car/A/get_log", param).then(
                    res => {
                        console.info('show log now')
                        this.car_log = res.data;
                        console.log(this.car_log);      
                        if (this.car_log != ''){
                            this.new_log = true;
                            console.log(this.new_log);
                        }
                        
				        if (this.tableData == undefined ) {
                            this.tableData = new Array();  // reset this row
                            // console.info('if 1');
                        }
                        if (this.new_log==true){   
                                               
                                // this.car_log="How are you\nToday?";
                                console.log(typeof(this.car_log));
                                this.log_spice = this.car_log.split("\\n', '");
                                console.log(this.log_spice.length);
                                // console.log(this.log_spice[0]);
                                for(var i=0;i<(this.log_spice.length);i++){
                                    console.info(i);
                                    let obj = {};
                                    obj.log=this.log_spice[i];
                                    console.log(obj.log);
                                    this.tableData.push(obj);
                                }
                                
                                
                                // console.info('if 2');					        
				        }
                        
				        this.new_log = false;
                        
                    }
                ).catch(res => {
                    console.log(res.data.res)
                })
            },

            skg(){
                // this.$router.replace('/skg')

                // this.$router.push('/skg')
                let jumppage = this.$router.resolve({name:'skg'})
                window.open(jumppage.href,'_blank')
            },

            jumptest(){
                // this.$router.replace('/skg')

                // this.$router.push('/blue')
                let jumppage = this.$router.resolve({name:'blue', query:{id:1}})
                window.open(jumppage.href,'_blank')
            },

            // jump2(){
            //     // window.open('skg.html')
            // },

            // jump3(){
            //     this.$router.push('/skg')
            //     const jumppage = this.$router.resolve({name:'/skg', param:{id:e}})
            //     window.open(jumppage.href,'_blank')
            // }
            
        },

        mounted() {
            //显示当前日期时间
            let _this = this// 声明一个变量指向Vue实例this，保证作用域一致
            this.timer = setInterval(() => {
                _this.date = new Date(); // 修改数据date
                _this.show_log();
                // _this.addRow();
            }, 100)

            // this.show_log();

        },

        beforeDestroy() {
            if (this.timer) {
                clearInterval(this.timer); // 在Vue实例销毁前，清除我们的定时器
            }
        }

    }

    // var time
    //   // 创建一个元素节点
    // function insertAfter( newElement, targetElement ){ // newElement是要追加的元素targetElement 是指定元素的位置
    //     var parent = targetElement.parentNode; // 找到指定元素的父节点
    //     parent.appendChild( newElement, targetElement );
    // };
    // function log(){
    //     clearTimeout(time) // 清空定时器
    //     var log_null = 0 //存放空日志次数
    //     var div = document.getElementById('log_list') //找到存放日志的块
    //     div.innerHTML = "<div id='log_text'></div>" // 每次跑清空div内内容
 
    //     $.post('/generation_log',{},function (){
    //     }) //请求生成日志接口
    //     // 生成定时器
    //     time = setInterval(function (){
    //         $.get('/get_log',{},function (data){ //请求获取日志接口获取日志
    //             if (data.log_type == 3){ //如果获取的是空日志log_null次数加1
    //                 log_null ++
    //                 if (log_null >= 5){
    //                     clearTimeout(time) //如果连续10次获取的都是空日志清除定时任务
    //                 }
    //                 return
    //             }
    //             if (data.log_type == 2){ //如果获取到新日志
    //                 for (i=0;i<data.log_list.length;i++){ //遍历日志
    //                     var p = document.createElement("p") //生成一个p标签
    //                     p.innerHTML = data.log_list[i] //日志存放到P标签内
    //                     var header = document.getElementById('log_text')
    //                     insertAfter(p,header) //将p标签添加到log_text div中
    //                     div.scrollTop = div.scrollHeight //滚动条实时显示到底部
    //                 }
    //                 log_null = 0 //日志为空次数清0
    //             }
 
    //         })
    //     },1000) //每1秒钟执行一次
    // }
    // document.getElementById('button').addEventListener("click",log) //点击开始按钮开始执行
</script>



<style scoped>
    #car-status-area {
        margin-left: 20%;
        margin-right: 20%;
    }
    #car-operation {
        margin-top: 20px;
    }
    #car-img {
        width: 800px;
        height: 300px;
        margin: 20px;
    }

    .el-header {
    background-color: #B3C0D1;
    color: #333;
    line-height: 60px;
    }
  
    .el-aside {
    color: #333;
    }
</style>