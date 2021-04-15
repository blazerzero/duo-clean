import axios from 'axios'

export default axios.create({
    baseURL: 'https://api.worksbythepg.com/duo/api',
    headers: { 'Cache-Control': 'no-cache' },
})