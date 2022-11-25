/*
 * Jenkinsfile to pull the source code from git, build a docker image
 * using a Dockerfile and push that image to a registry.
 */


pipeline {

  agent any

  environment {
    dockertag = 'datalabauth/twitter-bitcoin-api'
    registry = 'https://registry.hub.docker.com'
    registry_credentials = 'dockerhub'
  }

  // you probably don't need to edit anything below this line
  stages {
           
    stage('Checkout the source code') {
      steps {
        checkout scm
      }
    }

    stage('Build') {
      steps {
        script {
          image = docker.build("$dockertag")
        }
      }
    }

    stage('Push') {
      steps {
        script {
          docker.withRegistry(registry, registry_credentials) {
            image.push()
          }
        }
      }
    }
  }
}


