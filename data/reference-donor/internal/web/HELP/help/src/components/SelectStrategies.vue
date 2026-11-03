<script>
import axios from 'axios'
export default {
  props: {
    show: Boolean
  },
  data(){
    return {
      params: {
        type: "strategyFromDatabank",
        project: "",
        databank: "",
        strategies: "",
        projectConfigs: [],
        programLogs: [],
        file: ""
      },
      projects: [],
      databanks: []
    }
  },
  methods:{
    async loadProjects(){
        let result = await axios({
            method: 'post',
            url: '/help/loadProjects'
        });
        return result.data;
    },
    async loadStrategies(projectName, databankName){
        let result = await axios({
            method: 'post',
            url: '/help/loadStrategies?projectName=' + projectName + "&databankName=" + databankName
        });
        return result.data;
    },
    async loadDatabanks(projectName){
        let result = await axios({
            method: 'post',
            url: '/help/loadDatabanks?projectName=' + projectName
        });
        return result.data;
    },
    async projectChanged(){
        let result = await this.loadDatabanks(this.params.project);
        let databanks = []
        for(let databank of result.databanks){
            databanks.push({
                key: databank.name,
                value: databank.name
            })
        }
        this.databanks = databanks;
    }
  },
  async mounted(){
    let result = await this.loadProjects();
    let projects = []
    for(let project of result.projects){
        projects.push({
            key: project.projectName,
            value: project.projectName
        })
    }
    this.projects = projects;
  }
}
</script>

<template>
  <Transition name="modal">
    <div v-if="show" class="modal-mask">
      <div class="content">
        <div style="margin-bottom:15px">
            Select strategies that you want to submit
        </div>
        <div class="strategies">  
            <div>
                <input type="checkbox"> Name
            </div>
        </div>
        <div style="margin-top:15px" align="right" id="buttons" class="selection">
          <span @click="$emit('close')" class="close">Close</span>
          <button @click="save()" class="save">Save</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style>
  .modal-mask {
    position: fixed;
    z-index: 9998;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content:center;
    transition: opacity 0.3s ease;
  }
  .content{
    background: white;
    padding: 30px;
    width: auto;
    transition: all 0.3s ease;
  }
  #chooseStrategies{
    border: 1px solid grey;
    align-items: center;
    justify-content: center;
    display: flex;
    border-radius: 3px;
    cursor: pointer;
  }
  .strategies{
    height: 30vh;
    max-height:30vh;
    overflow: auto;
  }
  #buttons{
      border-top: 1px solid grey;
      padding-top: 15px;
  }
  #buttons .close{
      cursor: pointer
  }
  #buttons .save{
      background: rgb(0, 158, 231);
      padding: 6px 15px 6px 15px;
      color: white;
      border: none;
      margin-left: 9px;
      cursor: pointer;
  }

  .modal-enter-from {
    opacity: 0;
  }

  .modal-leave-to {
    opacity: 0;
  }

  .modal-enter-from .content,
  .modal-leave-to .content {
    -webkit-transform: scale(1.1);
    transform: scale(1.1);
  }
</style>