
stage('Build') {
    steps {
        sh '''
            docker build -t document-management:${BUILD_NUMBER} .
            docker tag document-management:${BUILD_NUMBER} document-management:latest
        '''
    }
}
