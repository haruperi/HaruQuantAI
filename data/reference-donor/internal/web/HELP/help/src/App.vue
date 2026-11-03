<template>
  <QNA v-if="showPage == 'qna'" @changePage="changePage"/>
  <OpenTicket v-if="showPage == 'openTicket'" @changePage="changePage"/>
  <AddFile v-if="showPage == 'addFile'" @changePage="changePage"/>
</template>

<script>
import QNA from './components/QNA.vue'
import OpenTicket from './components/OpenTicket.vue'
import AddFile from './components/AddFile.vue'

export default {
  name: 'App',
  components: {
    QNA,
    OpenTicket,
    AddFile
  },
  methods: {
    changePage(page){
      this.showPage = page;
    },
  },
  data () {
    return {
      showPage: 'qna',
    }
  },
}
</script>

<style>
body{
  margin: 0px;
  padding: 0px;
}
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  padding: 15px;
}
</style>
