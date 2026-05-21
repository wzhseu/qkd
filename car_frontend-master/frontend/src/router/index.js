import Vue from 'vue'
import Router from 'vue-router'
import test from '@/pages/test'
import page2 from '@/pages/page2'
import skg from '@/pages/skg'
import Car from '@/pages/Car'

Vue.use(Router)

export default new Router({
  routes: [
  {
    path: '/test',
    name: 'test',
    component: test,
  },
  {
    path: '/page2',
    name: 'page2',
    component: page2,
  },
  {
    path: '/skg',
    name: 'skg',
    component: skg,
  },
  {
    path: '/',
    name: 'Car',
    component: Car,
  }
]
})
