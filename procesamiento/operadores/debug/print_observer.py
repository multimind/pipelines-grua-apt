from rx import Observable

class PrintObserver(Observable):

    def on_next(self, value):
        pass
        #print(value)

    def on_completed(self):
        print("Done!")

    def on_error(self, error):
        print("Error Occurred: {0}".format(error))
