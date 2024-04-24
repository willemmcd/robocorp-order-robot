from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    open_robot_order_website()
    orders = get_orders()
    process_orders(orders)    
    archive_receipts()

def open_robot_order_website():
    """ Navigate to the robot order website and """
    browser.configure(browser_engine="firefox")
    page = browser.page()
    page.goto("https://robotsparebinindustries.com/#/robot-order")

def get_orders():
    """ Download the csv file with the contained orders """
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)
    library = Tables()
    order_data = library.read_table_from_csv("orders.csv", columns=["Order number","Head","Body","Legs","Address"])
    return order_data                                     

def close_annoying_modal():
    """ Accept the terms popup before order form is available """
    page = browser.page()
    page.click("button:text('Yep')")

def process_orders(orders):
    """ Loop through each order item and process order  """
    print("looping through orders")
    first = True
    for order in orders:
        if not first:
            click_order_another_robot()
        else:
            first = False

        print("Order no = " + str(order["Order number"]))
        close_annoying_modal()
        fill_the_form(order)
        order_success = submit_order()
        if order_success is True:
            pdf_file_name = store_receipt_as_pdf(order["Order number"])
            screenshot = screenshot_robot(order["Order number"])
            embed_screenshot_to_receipt(screenshot, pdf_file_name)
            print("Order processed successfully")
        else:
            print("Order could not be placed after retrying 10 times.")
            #Alert another system or send email to responsible person?

def fill_the_form(order):
    """ Fill all the required form fields with order data """
    page = browser.page()
    page.select_option("#head", str(order["Head"]))
    page.set_checked(selector="#id-body-" + order["Body"], checked=True)
    locator = page.get_by_placeholder("Enter the part number for the legs")
    locator.fill(order["Legs"])
    page.fill("#address", order["Address"])
    page.click("button:text('Preview')")
    

def submit_order():
    """ Click the order button and check if order was submitted successfully """
    order_success = False
    page = browser.page()
    page.click("button:text('ORDER')")
    #see if we have an error dialog popped up
    alert_shown = check_for_alert()
    retry_max = 10
    retry = 0   
    
    while alert_shown and retry < retry_max:
        print("Alert shown!")
        retry = retry + 1
        page.click("button:text('ORDER')")
        alert_shown = check_for_alert()        

    if alert_shown is False:
        order_success = True
    
    return order_success

def click_order_another_robot():
    page = browser.page()
    page.click("button:text('ORDER ANOTHER ROBOT')")

def check_for_alert():
    alert_shown = True
    try:
        page = browser.page()
        alert_locator = page.get_by_role("alert")
        alert_elements = alert_locator.all()

        for alert_element in alert_elements:
            class_attribute = alert_element.get_attribute("class")
            
            if "alert-danger" in class_attribute:
                break
            elif "alert-success" in class_attribute or "alert-light" in class_attribute:
                alert_shown = False
                break
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")

    return alert_shown

def store_receipt_as_pdf(order_number):
    """ Store the pdf file for the order created """
    pdf_file_name = "output/receipts/OrderReceipt_" + str(order_number) + ".pdf"
    page = browser.page()
    results_html = page.locator("#receipt").inner_html()
    pdf = PDF()
    pdf.html_to_pdf(results_html, pdf_file_name)
    return pdf_file_name
    

def screenshot_robot(order_number):
    """ Takes a screenshot of the robot """
    screenshot = "output/" + str(order_number) + "_screenshot.png";
    page = browser.page()
    div_element = page.query_selector("#robot-preview-image")
    div_element.screenshot(path=screenshot)
    return screenshot


def embed_screenshot_to_receipt(screenshot, pdf_file):
    """ Embed the screenshot to the pdf receipt """
    list_of_files = [
        screenshot
    ]
    pdf = PDF()
    print(screenshot)
    print(pdf_file)
    pdf.add_files_to_pdf(
        files=list_of_files,
        target_document=pdf_file,
        append=True
    )
    
def archive_receipts():
    """ Let's zip all the receipts """
    lib = Archive()
    lib.archive_folder_with_zip('output/receipts', 'output/receipts.zip', recursive=True)
    
