<template>
  <div id="app" class="home">

    <!-- <vue-particles color="#dedede" :particleOpacity="0.7" :particlesNumber="40" shapeType="star" :particleSize="4"
      linesColor="#FFFFFF" :linesWidth="2" :lineLinked="true" :lineOpacity="0.4" :linesDistance="150" :moveSpeed="3"
      :hoverEffect="true" hoverMode="grab" :clickEffect="true" clickMode="push" class="cash">
    </vue-particles> -->
    <div class="background">
       <img src="../assets/images/bg.jpg" width="100%" height="100%" alt="" />
    </div>
   

    <div class="scanboardWp animsition">
      <div id="top">
        <div class="wp clearfix">
          <div class="left pageTit"></div>

          <div class="center topLogo">
            <a href="#" style="font-size: 50px">Car Simulation</a>
          </div>

          <div id="time" style="color: aliceblue ;">
            <h4>Time Now:</h4>
            <p>{{ date | dateFormat() }}</p>
          </div>

        </div>
      </div>



      <div id="main" class="wp clearfix">
        <div class="left">
          <div class="item billState">
            <div class="itemTit">
              <span class="border-yellow">本机信息</span>
            </div>
            <div class="itemCon">
              <br /><br /><br />
              <p align="center"><img src="../assets/images/car.png" height="80px" alt="" /></p>
              <div align="center">
                <font size="5px" color="#FFFFFF">{{ name }}</font>
              </div>
              <br /><br />
              <div class="infoAuth">
                <div class="authentication" align="center">
                  <p><strong>设备名称：</strong><strong>{{ name }}</strong></p>
                  <br />
                  <p><strong v-if="car_open ==false">设备状态：...</strong></p>
                  <p><strong v-if="car_open ==true">设备状态：已启动</strong></p>
                  <br />
                  <p><strong>DAA直接匿名认证状态: </strong></p>
                  <br>
                  <p><strong v-if="DAA == true">认证成功！</strong>
                    <strong v-if="DAA == false">尚未认证！</strong>
                  </p>
                  <br />
                  <p><strong>视频传输状态: </strong></p>
                  <br>
                  <p><strong v-if="videoTransferState == true">量子加密传输成功！</strong>
                    <strong v-if="videoTransferState == false && DAA == true">正在传输……</strong>
                    <strong v-if="videoTransferState == false && DAA == false">等待传输！</strong>
                  </p>
                </div>
              </div>
              <!-- <div class="infoPie">
                <ul class="clearfix">
                  <li class="color-yellow">
                    <span class="border-yellow">233</span>
                    <p>终端设备数</p>
                  </li>
                  <li class="color-blue">
                    <span class="border-blue">233</span>
                    <p>总通信次数</p>
                  </li>
                  <li class="color-green">
                    <span class="border-green">233</span>
                    <p>密钥生成量</p>
                  </li>
                </ul>
              </div> -->
            </div>
          </div>
        </div>

        <div class="center">
          <div class="centerWp">
            <div class="item itembg">
              <div class="itemTit">
                <span class="border-blue">通信过程</span>
              </div>
              <div class="itemCon" align="center">
                <font color="white" size="6px">{{ startFlag }}</font>
                <br /><br />


                <div v-if="videoState == true">
                  <video ref="myVideo" :poster="poster" src="../../../backend/app/q_transfer/video.mp4"
                    :controls="controls" class="video" loop="loop" width="90%" height="90%">
                  </video>
                </div>

                <!-- <div v-if="videoState == true">
                  <img :src="video_feed">
                </div> -->

                <div v-if="videoState == false">
                  <br><br><br><br><br>
                  <div class="infoAuth">
                    <div class="authentication" align="center">
                      <p><strong>传输尚未进行或尚未完成</strong></p>
                      <br>
                      <p><strong>无视频信号</strong></p>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>

          <el-button type="primary" style="width:80%;font-size:20px;" @click="log" round>启动</el-button>
          <div id="jump" margin="20px">
            <el-button type="primary" style="width:80%;font-size:20px;" @click="video_call" round>视频通信</el-button>
          </div>
            <div id="jump" margin="20px">
            <el-button type="primary" style="width:80%;font-size:15px;" @click="skg" round>无线信道密钥探测</el-button>
          </div>
          <!-- <div class="exp">
            <a-row>            <a-col offset='9' span='10'> 
                <a-button class="expButton"  @click="log">
                  实验开始
                </a-button>
              </a-col> 
            </a-row>
          </div>  -->

        </div>

        <div class="right">
          <div class="item itembg">
            <div class="itemTit">
              <span class="border-green">通信状态</span>
            </div>
            <div class="itemCon">
              <!-- <div class="infoAuth">
                <div class="authentication" align="center">
                  <p><strong>本机当前通信状态：</strong></p>
                  <br>
                  <p><strong v-if="!transmission">未在通信或已通信完毕！</strong>
                    <strong v-if="transmission">正在通信！</strong></p>
                  <br><br><br>
                  <p><strong>本机总通信次数：</strong></p>
                </div>
              </div> -->

              <div class="item billState">
                <div class="itemTit">
                  <span class="border-yellow">实时日志更新</span>
                </div>
              </div>

              <!-- <div class="itemCon" > -->
              <!-- <div class="StateBox"> -->
              <!-- <div id="FontScroll" height="1000"> -->
              <!-- <a-row class="stateTitle">
                        <a-col offset='2' span='9'>
                          当前状态
                        </a-col>
                        <a-col offset='2' span='9'>
                          更新时间
                        </a-col>
                      </a-row> -->

              <!-- <vue-seamless-scroll style="background-color: rgba(0,0,0,0.3);" class="seamless-warp" height="1000"> -->

              <div class="user_skills" max-height="auto">

                <el-table id="editTable" :data="tableData" :row-class-name="tableRowClassName" :show-header="false" height="400"
                  max-height="auto" style="width:100%; height:100%; color: aliceblue;"
                  :header-cell-style="{ background: 'rgb(10, 20, 45)', color: '#ffd220' }"
                  @scroll.native="handleTableScroll">


                  <el-table-column fixed prop="log" label="LOG">
                  </el-table-column>

                </el-table>
              </div>
              <!-- </vue-seamless-scroll> -->

              <!-- <vue-seamless-scroll :data="tableData" class="seamless-warp">
                  <div class="state">
                    <a-row class="liststyle" v-for="item in tableData" :key="item.id">
                      <a-col class="title" v-text="item.log" offset='2' span='9'></a-col>
                      <a-col class="log" v-text="item.log" offset='2' span='9'></a-col>
                    </a-row>
                  </div>

                </vue-seamless-scroll> -->

              <!-- </div> -->
              <!-- </div> -->
              <!-- </div> -->

              <!-- <el-table :data="tableData" style="width: 100%"   ref="tb" :row-class-name="tableRowClassName" @current-change="handleRadioChange">
                    <el-table-column fixed prop="log" label="LOG" ></el-table-column>
                </el-table> -->

              <!-- <el-table
                  :data="tableData"
                  style="width: 100%"
                  height="250">
                  <el-table-column
                    fixed
                    prop="log"
                    label="LOG"
                    >
                  </el-table-column>
                  
                </el-table> -->

              <!-- </div> -->

              <!-- <div align="center">
                <div class="infoPie">
                  <ul class="clearfix">
                    <li class="color-yellow">
                      <span class="border-yellow">{{ count }}</span>
                    </li>
                  </ul>
                </div>
              </div> -->

            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<script>
export default {
  // name: 'CommonVideo',
  props: {
    poster: {
      type: String,
      required: false,
      default: ''
    },
    controls: {
      type: Boolean,
      required: false,
      default: true
    }
  },
  data() {
    return {
      name: "Car B",
      DAA: false,
      videoState: true,
      videoTransferState: false,
      photoState: false,
      transmission: false,
      count: 8,
      startFlag: "本机所发送的视频: ",

      textarea: '',
      pic: "",
      pageTitle: '车联网终端可视化界面',
      car_status: "等待连接……",
      car_open: false,
      car_log: " ",
      new_log: false,
      log_spice: new Array(),
      date: new Date(),
      // 给一个默认行
      tableData: [
        { 'log': 'info: Hello!' },
      ],
      // videoSrc: require('../../../backend/app/q_transfer/video.mp4')
      videoSrc: "../../../backend/app/q_transfer/video.mp4"

    }

  },



  filters: {
    dateFormat() {
      // var val=JSON.parse(time);
      var date = new Date();
      var year = date.getFullYear();
      var month = date.getMonth();
      var month = date.getMonth() + 1 < 10 ? "0" + (date.getMonth() + 1) : date.getMonth() + 1;
      var day = date.getDate() < 10 ? "0" + date.getDate() : date.getDate();
      var hours = date.getHours() < 10 ? "0" + date.getHours() : date.getHours();
      var minutes = date.getMinutes() < 10 ? "0" + date.getMinutes() : date.getMinutes();
      var seconds = date.getSeconds() < 10 ? "0" + date.getSeconds() : date.getSeconds();
      // 拼接
      return year + "-" + month + "-" + day + " " + hours + ":" + minutes + ":" + seconds;
    }
  },

  methods: {
    start() {
      setTimeout(() => {
        this.startFlag = "本机所发送的视频: "
        this.transmission = true
      }, 2000);
    },

    // Aut() {
    //   setTimeout(() => {
    //     this.axios.post("/car/A/Aut", param).then(
    //       res => {
    //           console.info('Authentication')
    //           if (this.car_log != ''){
    //               this.DAA = true;
    //           }
    //         })


    //   }, 2000);
    // },

    // VDT: ViDeo Transfer
    // VDT() {

    //   if (this.DAA == true) {

    //     this.axios.post("/car/A/VDT", param).then(
    //       res => {
    //         console.info('VDT start')
    //       }
    //     ).catch(res => {
    //     })
    //     this.videoState = true;
    //   }

    // },

    end() {
      setTimeout(() => {
        // this.videoState = true
        this.transmission = false
        this.count = 9
      }, 2000);
    },

    tableRowClassName({ row, rowIndex }) {
      if (rowIndex >= 0) {
        return 'common-row';
      }
    },

    // handleTableScroll(){
    //   const tableBody = this.$refs.table.$el.querySelector('.el-table__body-wrapper')
    //   const isBottom = tableBody.scrollTop + tableBody.clientHeight === tableBody.scrollHeight

    // },

    log() {
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
      // this.DAA=true;
    },

    video_call() {
      var param = {
        "car": this.textarea
      }
      this.axios.post("/car/A/video_call", param).then(
        res => {
          console.info('ask video call...')
        }
      ).catch(res => {
      })
    },

    show_log() {
      var param = {
        "car": this.textarea
      }
      this.axios.post("/car/A/get_log", param).then(
        res => {
          // console.info('show log now')
          this.car_log = res.data;
          console.log(this.car_log);
          if (this.car_log != '') {
            this.new_log = true;
            console.log(this.new_log);
          }

          if (this.tableData == undefined) {
            this.tableData = new Array();  // reset this row
            // console.info('if 1');
          }
          if (this.new_log == true) {

            // this.car_log="How are you\nToday?";
            console.log(typeof (this.car_log));
            this.log_spice = this.car_log.split("\\n', '")
            // .join("\\n\", '");

            console.log(this.log_spice.length);
            // console.log(this.log_spice[0]);
            for (var i = 0; i < (this.log_spice.length); i++) {
              // console.info(i);
              let obj = {};
              obj.log = this.log_spice[i];
              console.info(obj.log);
              setTimeout(() =>{
                this.tableData.unshift(obj);
              },300);             
              
              // this.$nextTick(() => {
              //   this.$refs.tableData.bodyWrapper.scrollTop = this.$refs.tableData.bodyWrapper.scrollHeight
              // });

              if (this.log_spice[i].includes('车B加密发送视频文件', 1) == true) {
                console.info("Verification Done!");
                this.DAA = true;
                this.axios.post("/car/A/VDT", param).then(  //if DAA is done, go to VDT
                  res => {
                    console.info('VDT start')
                    const token = res.data;
                    console.info("token:", res.data);
                    if (token == "True") {
                      this.videoTransferState = true;
                    }

                  }
                ).catch(res => {
                })
              }

              //////////////////////video call//////////////////////
              // if (this.log_spice[i].includes('Verification Done!', 1) == true) {
              //   console.info("Verification Done!");
              //   this.DAA = true;
              //   this.videoState = true;
              // }

            }


            // console.info('if 2');					        
          }

          this.new_log = false;

        }
      ).catch(res => {
        console.log(res.data.res)
      })
    },

    skg() {
      // this.$router.replace('/skg')

      // this.$router.push('/skg')
      let jumppage = this.$router.resolve({ name: 'skg' })
      window.open(jumppage.href, '_blank')
    },

    videoDisplay() {
      // console.info(this.videoState)
      // if (this.photoState = true){
      // this.$refs.myVideo.src = this.videoSrc
      this.$refs.addEventListener('play', this.handlePlay);
      this.$refs.addEventListener('pause', this.handlePause);
      // this.$refs.myVideo.addEventListener('play', () => {})
      // this.$refs.myVideo.addEventListener('parse', ()=> {})

      // }

    },

    handlePlay() {
      this.$refs.media.play();
      this.isPlay = true
    },

    handlePause() {
      this.$refs.media.pause();
      this.isPlay = false
    }

  },

  mounted() {
    //显示当前日期时间
    let _this = this;// 声明一个变量指向Vue实例this，保证作用域一致
    this.timer = setInterval(() => {
      _this.date = new Date(); // 修改数据date
      _this.show_log();
      // _this.addRow();
    }, 100);

    // this.$watch('DAA', function(newValue, oldValue){
    //   console.log(newValue);
    // });

    // this.$watch('videoState', function(newValue, oldValue){
    //   console.log(newValue);
    // });


    console.info('DAA:', this.DAA);
    console.info('videoState:', this.videoState);

    this.start();
    console.info('start');
    console.info('DAA:', this.DAA);
    console.info('videoState:', this.videoState);

    // this.VDT();
    // console.info('VDT');
    // console.info('DAA:', this.DAA);
    // console.info('videoState:', this.videoState);

    // this.VDT();
    // console.info("VDT start!")

    this.videoDisplay();
    console.info('videoDisplay');
    console.info('DAA:', this.DAA);
    console.info('videoState:', this.videoState);

    this.end();
    console.info('end');
    console.info('DAA:', this.DAA);
    console.info('videoState:', this.videoState);

  },


  beforeDestroy() {

    if (this.timer) {
      clearInterval(this.timer); // 在Vue实例销毁前，清除我们的定时器

    }

  }


};
</script>

<style scoped>
@import "../assets/css/base.css";
@import "../assets/css/reset.css";


.background{
  position: fixed;
  z-index: -1 ;
  width: 100%;
  height: 100%;
 
}

.cash {
  position: fixed;
  top: 18px;
  width: 100%;
}

.seamless-warp {
  height: 229px;
  overflow: hidden;
  font-size: 15px;
}

#experiment {
  background-image: url("../assets/images/graph.png");
  background-size: 100% 100%;
  background-position: center;
  /* width: 540px;
  height: 300px; */
  width: 830px;
  height: 350px;
  text-align: center;
}
</style>



<style>
/* 屏幕小于1440px */
@media screen and (max-width: 1440px) {
  .add {
    width: 260px;
  }
}

/* 屏幕等于1440px */
@media screen and (max-width: 1440px) and (min-width: 1440px) {
  .add {
    width: 348px;
  }
}

/* 屏幕大于1440px */
@media screen and (min-width: 1441px) {
  .add {
    width: 348px;
  }
}
</style>
