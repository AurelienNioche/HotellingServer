def main():

    from config_files_manager import ConfigFilesManager

    ConfigFilesManager.run()

    from hotelling_server import model

    m = model.Model()
    m.run()


if __name__ == "__main__":

    main()
