using System;
using Microsoft.Office.Interop.Word;
using System.IO;
using System.Linq;

namespace HtmlToDocx
{
    class Program
    {
        static string path = @"C:\Users\zakhej_hrg\HRG Repos\cf-tools-27.06\word";
        static void SaveHTMLAsDoc(string fname)
        {
            string f_in = fname;
            string f_out = Path.Combine(Path.GetDirectoryName(fname), Path.GetFileNameWithoutExtension(fname) + ".doc");

            Application word = new Application();
            word.Visible = false;
            var wordDoc = word.Documents.Open(f_in, false, true);
            wordDoc.SaveAs(f_out, WdSaveFormat.wdFormatDocument);

            word.Quit();
        }
        static void Main(string[] args)
        {
            var htmlFiles = Directory.EnumerateFiles(path, "*.*", SearchOption.TopDirectoryOnly)
                                .Where(s => Path.GetExtension(s) == ".html" && !Path.GetFileName(s).StartsWith("~")).ToList();

            for(var i = 0; i < htmlFiles.Count; ++i)
            {                
                SaveHTMLAsDoc(htmlFiles[i]);
                Console.Write("\rSaved as HTML: {0}/{1}               ", i+1, htmlFiles.Count);
            }

        }
    }
}
