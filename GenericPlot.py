import matplotlib.pyplot as plt


class GenericPlot:
    RENDER_ROOT = "render/"
    save = True
    show = True

    @classmethod
    def render(cls, xl=None, yl=None, title=None, date=None, legend=True):
        dated_title = None

        if legend is True:
            plt.legend()

        if title is not None:
            dated_title = title + "" if date is None else date.strftime("%m-%d-%y") + " " + title
            plt.title(dated_title)

        if xl is not None:
            plt.xlabel(xl)

        if yl is not None:
            plt.ylabel(yl)

        if GenericPlot.save:
            filename = "untitled" if title is None else dated_title.replace(" ", "_").lower()
            plt.savefig(GenericPlot.RENDER_ROOT + filename)

        if GenericPlot.show:
            plt.show()

        plt.clf()
