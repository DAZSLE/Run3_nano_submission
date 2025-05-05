from dbs.apis.dbsClient import DbsApi

dbs = DbsApi("https://cmsweb.cern.ch/dbs/prod/global/DBSReader")

dbs.listDatasets(dataset="/MinBias/Summer*/*")
