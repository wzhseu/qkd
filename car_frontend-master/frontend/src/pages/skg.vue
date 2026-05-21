<template>
    <div>

        
        <div id="buttons">
            <el-button type="primary" style="width:80%" @click="autorun" round>AUTO RUN</el-button>
        </div>
        <iframe
        name="iframe"
        id="iframeComponent"
        frameborder="0"
        width="100%"
        height="1000px"
        src="../../static/skg.html"
        ></iframe>

       

    </div>

   


</template>

<script>
    export default {
        name: 'skg',
        data() {

            return {
                
            }
                
        },
        methods:{
            autorun(){
                this.axios.post("/car/A/autorun", param).then(
                    res => {
                        console.info('hello hello hello')
                    }
                ).catch(res => {
                    console.log(res.data.res)
                })
            },
        }
    }
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