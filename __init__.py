import io
import csv
from flask import Flask, render_template, request, make_response
app = Flask(__name__)

# @app.route('/')
# def home():
#     return render_template('hello.html')


@app.route('/', methods=['GET', 'POST']) #allow both GET and POST requests
def form_example():
    if request.method == 'POST':  #this block is only entered when the form is submitted
        org = request.form.get('github_org')
        csvList = [org]
        return "<h1>The GitHub org is: {}</h1>".format(org)
        # si = io.StringIO()
        # cw = csv.writer(si)
        # cw.writerows(csvList)
        # output = make_response(si.getvalue())
        # output.headers["Content-Disposition"] = "attachment; filename=export.csv"
        # output.headers["Content-type"] = "text/csv"
        # return output

    return '''<form method="POST">
                  GitHub Org URL: <input type="text" name="github_org">
                  <input type="submit" value="Submit"><br>
              </form>
              <p>It may over 1 minute for the csv to be generated.<p>'''

if __name__ == "__main__":
    app.run(debug=True)