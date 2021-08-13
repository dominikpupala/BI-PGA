#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gimp, gimpplugin, math, array
from gimpenums import *
import gtk, gimpui, gimpcolor
from gimpshelf import shelf

class channels_color_adjust_plugin(gimpplugin.plugin):
    def start(self):
        gimp.main(self.init, self.quit, self.query, self._run)

    def init(self):
        pass

    def quit(self):
        pass

    def query(self):
        gimp.install_procedure(
            "channels_color_adjust_plugin_main",
            "Color channels adjustment.",
            "Extension for RGB channels adjustment.",
            "Dominik Pupala",
            "Dominik Pupala",
            "2020",
            "<Image>/Filters/Color channels adjustment (pupaldom)",
            "RGB*, GRAY*",
            PLUGIN,
            [
                (PDB_INT32, "run_mode", "Run mode"),
                (PDB_IMAGE, "image", "Input image"),
                (PDB_DRAWABLE, "drawable", "Input drawable"),
			],
            []
        )

    def channels_color_adjust_plugin_main(self, run_mode, image, drawable):
        self.image = image
        self.drawable = drawable
        self.create_dialog()

        gimp.pdb.gimp_image_undo_group_start(self.image)
        
        if run_mode == RUN_INTERACTIVE:
            self.dialog.run()
        else:
            self.ok_clicked(None)
        
        gimp.pdb.gimp_image_undo_group_end(self.image)
        gimp.displays_flush()

    def create_dialog(self):
        # window
        self.dialog = gimpui.Dialog("Color channels adjustment", "color_channels_adjustment_dialog")

        self.table = gtk.Table(5, 20, False)
        self.table.set_row_spacings(8)
        self.table.set_col_spacings(16)
        self.table.show()

        # combobox
        self.label_selection = gtk.Label("Adjust:")
        self.label_selection.show()
        self.table.attach(self.label_selection, 1, 2, 1, 2)

        self.combobox_selection = gtk.combo_box_new_text()
        for a, f in self.actions: 
           self.combobox_selection.append_text(a)
        self.combobox_selection.connect("changed", self.selection_changed)
        self.combobox_selection.set_entry_text_column(0)
        self.combobox_selection.set_active(0)
        self.combobox_selection.show()
        self.table.attach(self.combobox_selection, 2, 19, 1, 2)

        # slider
        self.label_filter = gtk.Label("Value:")
        self.label_filter.show()
        self.table.attach(self.label_filter, 1, 2, 2, 3)

        self.adj = gtk.Adjustment(0, -255, 255, 0.1, 0.1, 0)
        self.slider_value = gtk.HScale(self.adj)
        self.slider_value.set_digits(0)
        self.slider_value.set_value(0)
        self.slider_value.show()
        self.table.attach(self.slider_value, 2, 19, 2, 3)

        # inner frames
        self.dialog.vbox.hbox1 = gtk.HBox(True, 0)
        self.dialog.vbox.hbox1.show()
        self.dialog.vbox.pack_start(self.dialog.vbox.hbox1, False, False, 0)
        self.dialog.vbox.hbox1.pack_start(self.table, True, True, 0)
        
        # buttons
        self.label_preview = gtk.Label("Preview:")
        self.label_preview.show()
        self.table.attach(self.label_preview, 1, 2, 4, 5)

        self.reload_button = gtk.Button("Reload")
        self.reload_button.connect("clicked", self.reload_clicked)
        self.reload_button.show()
        self.table.attach(self.reload_button, 2, 19, 4, 5)

        self.cancel_button = self.dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.cancel_button.connect("clicked", self.cancel_clicked)
        self.ok_button = self.dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.ok_button.connect("clicked", self.ok_clicked)

    def selection_changed(self, filter_box):
        self.action = filter_box.get_active()

    def reload_clicked(self, button):
        self.apply()

    def cancel_clicked(self, button):
        self.destroy_working_layer()

    def ok_clicked(self, button):
        self.apply()
        gimp.pdb.gimp_image_merge_down(self.image, self.layer, NORMAL_MODE)

    def apply(self):
        self.destroy_working_layer()

        # selection parameters
        bpp = self.drawable.bpp
        (bx1, by1, bx2, by2) = self.drawable.mask_bounds
        (bw, bh) = (bx2 - bx1, by2 - by1)
        (ox, oy) = self.drawable.offsets
        
        # source data
        src_rgn = self.drawable.get_pixel_rgn(bx1, by1, bw, bh, False, False)
        src_pxl = array.array("B", src_rgn[bx1:bx2, by1:by2])

        # creating working layer
        self.layer = gimp.Layer(self.image, "Preview", bw, bh, RGBA_IMAGE, 100, NORMAL_MODE)
        self.layer.set_offsets(bx1 + ox, by1 + oy)

        # destination data
        dst_rgn = self.layer.get_pixel_rgn(0, 0, bw, bh, True, True)
        dst_pxl = array.array("B", dst_rgn[0:bw, 0:bh])
        dst_bpp = 4 # always finalize as RGBA 

        self.image.add_layer(self.layer, 0)

        # iterate through the pixels and apply action
        gimp.progress_init("Applying adjustments")
        adjustment_value = self.slider_value.get_value()

        for i in range(0, bh):
            for j in range(0, bw):
                pos = (j + bw * i) * bpp

                arr_img = src_pxl[pos:(pos + bpp)]
                arr_rgb = gimpcolor.RGB(arr_img[0], arr_img[1], arr_img[2], arr_img[3] if bpp == 4 else 255)

                # apply selected action by accesing list of pairs
                arr_rgb = self.actions[self.action][1](self, arr_rgb, adjustment_value)

                arr_img[0:dst_bpp] = array.array("B", arr_rgb[0:dst_bpp])
                
                dst_pos = (j + bw * i) * dst_bpp
                dst_pxl[dst_pos:(dst_pos+dst_bpp)] = arr_img
            
            gimp.progress_update(float(i+1)/bh)
        gimp.progress_update(1.0)

        dst_rgn[0:bw, 0:bh] = dst_pxl.tostring()

        # update working layer
        self.layer.flush()
        self.layer.merge_shadow(True)
        self.layer.update(0, 0, bw, bh)
        
        gimp.displays_flush()

    def destroy_working_layer(self):
        if self.layer is not None:
            self.image.remove_layer(self.layer)
            self.layer = None
            gimp.displays_flush()

    def adjust_red(self, arr_rgb, adjustment_value):
        arr_rgb[0] = self.truncate_rgb(int(arr_rgb[0] + adjustment_value))
        return arr_rgb

    def adjust_green(self, arr_rgb, adjustment_value):
        arr_rgb[1] = self.truncate_rgb(int(arr_rgb[1] + adjustment_value))
        return arr_rgb

    def adjust_blue(self, arr_rgb, adjustment_value):
        arr_rgb[2] = self.truncate_rgb(int(arr_rgb[2] + adjustment_value))
        return arr_rgb

    def adjust_brightness(self, arr_rgb, adjustment_value):
        arr_hsv = arr_rgb.to_hsv()
        arr_hsv[2] = self.truncate_hsv(int(arr_hsv[2] + ((adjustment_value / 255) * 100)))
        arr_rgb = arr_hsv.to_rgb()
        return arr_rgb

    def adjust_contrast(self, arr_rgb, adjustment_value):
        temp = (259.0 * (255.0 + adjustment_value)) / (255.0 * (259.0 - adjustment_value))
        arr_rgb[0] = self.truncate_rgb(int((temp * (arr_rgb[0] - 128)) + 128))
        arr_rgb[1] = self.truncate_rgb(int((temp * (arr_rgb[1] - 128)) + 128))
        arr_rgb[2] = self.truncate_rgb(int((temp * (arr_rgb[2] - 128)) + 128))
        return arr_rgb

    def adjust_saturation(self, arr_rgb, adjustment_value):
        arr_hsv = arr_rgb.to_hsv()
        arr_hsv[1] = self.truncate_hsv(int(arr_hsv[1] + ((adjustment_value / 255) * 100)))
        arr_rgb = arr_hsv.to_rgb()
        return arr_rgb

    def truncate_rgb(self, value):
        return max(0, min(255, value))

    def truncate_hsv(self, value):
        return max(0, min(100, value))

    layer = None # reference to the working layer
    action = None # action index
    actions = [
        ("Red", adjust_red), 
        ("Green", adjust_green), 
        ("Blue", adjust_blue), 
        ("Brightness", adjust_brightness), 
        ("Contrast", adjust_contrast), 
        ("Saturation", adjust_saturation)
    ] # list of actions with their corresponding methods
    

if __name__ == '__main__':
    channels_color_adjust_plugin().start()