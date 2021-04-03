import React from 'react'
import { BrowserRouter as Router, Route } from 'react-router-dom'
import './css/App.css'
import { Interact } from './screens/Interact'
import { Start } from './screens/Start'
import { Welcome } from './screens/Welcome'

function App() {
  return (
    <Router>
        <Route path='/' exact component={Welcome} />
        <Route path='/start/' component={Start} />
        <Route path='/interact/' component={Interact} />
        {/* <Route path='/post-interaction/' component={PostInteraction} /> */}
    </Router>
  )
}

export default App
