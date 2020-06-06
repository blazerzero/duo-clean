import React, { Component } from 'react';

export default class Header extends Component {
    
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div className='home-header box-blur'>
                <span className='title'>DuoClean</span>
                {this.props.projectId !== 'TBD' && <p className='subtitle'>Project ID: {this.props.projectId}</p>}
            </div>
        )
    }
}