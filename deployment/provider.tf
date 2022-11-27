terraform {
  required_version = ">= 1.3.0"

  backend "remote" {
    organization = "hotosm"

    workspaces {
      name = "osm-stats"
    }
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.16.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "=3.3.2"
    }
  }
}


provider "azurerm" {
  features {}
}

provider "random" {

}

/*** LEGACY
provider "azurerm" {
  skip_credentials_validation = true
  version = "~> 1.29"
}
***/
